import os
import json
import time
from openai import OpenAI
from pydantic import BaseModel
from .models import TriageResult, LogAnalysisResult, ReproductionResult, FixPlanResult, ReviewResult
from . import tools

def get_client():
    # Points to Local Desktop Ollama
    return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

class UnifiedAgent:
    def __init__(self, role: str, instructions: str, model_name: str = "llama3.2"):
        self.role = role
        self.instructions = instructions
        self.model_name = model_name
        try:
            self.client = get_client()
        except:
            self.client = None

    def _get_tool_schema(self, func_name: str):
        if func_name == "read_file":
            return {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}
        if func_name == "search_files":
            return {"type": "object", "properties": {"directory": {"type": "string"}, "query": {"type": "string"}}, "required": ["directory", "query"]}
        if func_name == "write_test_script":
            return {"type": "object", "properties": {"script_path": {"type": "string"}, "code": {"type": "string"}}, "required": ["script_path", "code"]}
        if func_name == "run_test_script":
            return {"type": "object", "properties": {"script_path": {"type": "string"}, "args": {"type": "string"}}, "required": ["script_path"]}
        return {"type": "object", "properties": {}}

    def _execute(self, prompt: str, schema=None, available_tools=None, context: str = "") -> any:
        if not self.client:
            return self._mock_response(schema)
            
        messages = [
            {"role": "system", "content": f"Role: {self.role}\nInstructions: {self.instructions}"},
            {"role": "user", "content": f"Context: {context}\nTask: {prompt}"}
        ]
        
        kwargs = {
            "model": self.model_name,
            "temperature": 0.2,
        }
        
        if schema and not available_tools:
            kwargs["response_format"] = {"type": "json_object"}
            messages[0]["content"] += f"\nIMPORTANT: Output EXACTLY a JSON object matching this schema: {schema.model_json_schema()}"
            
        if available_tools:
            if schema:
                messages[0]["content"] += f"\nIMPORTANT: Output exactly a JSON object matching this schema at the end of your analysis: {schema.model_json_schema()}"
            
            openai_tools = []
            for t in available_tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.__name__,
                        "description": t.__doc__ if t.__doc__ else "Tool",
                        "parameters": self._get_tool_schema(t.__name__)
                    }
                })
            kwargs["tools"] = openai_tools
            
        kwargs["messages"] = messages
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            
            if available_tools:
                while message.tool_calls:
                    messages.append(message)
                    for tc in message.tool_calls:
                        func_name = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments)
                        except:
                            args = {}
                            
                        print(f"[{self.role}] calling tool: {func_name} with {args}")
                        if hasattr(tools, func_name):
                            tool_func = getattr(tools, func_name)
                            try:
                                result = str(tool_func(**args))
                            except Exception as e:
                                result = str(e)
                        else:
                            result = f"Tool {func_name} not found."
                            
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                        
                    kwargs["messages"] = messages
                    response = self.client.chat.completions.create(**kwargs)
                    message = response.choices[0].message
                    
            return message.content
            
        except Exception as e:
            print(f"[{self.role}] Local API Call failed: {e}. Is Ollama running?")
            return self._mock_response(schema)

    def _mock_response(self, schema):
        print(f"[{self.role}] Executing mock response...")
        if not schema: return "{}"
        if schema.__name__ == "TriageResult":
            return '{"symptoms": "Crashes", "expected_behavior": "Shouldn\'t crash", "actual_behavior": "Crashes", "environment": "Python 3.9+", "prioritized_hypotheses": ["Bad index", "Null check missing"]}'
        if schema.__name__ == "LogAnalysisResult":
             return '{"error_signature": "IndexError: list index out of range", "key_anomalies": ["Crash happens after processing 2 records"], "correlation": "Correlates with lines parsing"}'
        if schema.__name__ == "ReproductionResult":
             return '{"repro_script_path": "repro.py", "run_command": "python repro.py", "outcome": "IndexError", "is_minimal": true}'
        if schema.__name__ == "FixPlanResult":
             return '{"root_cause_hypothesis": "Not checking for empty lines", "patch_approach": "Add a length check before indexing", "impacted_files": ["repo/batch_processor.py"], "confidence": "HIGH", "verification_plan": "Run the repro script again"}'
        if schema.__name__ == "ReviewResult":
             return '{"approved": true, "reviewer_comments": "Looks good", "edge_cases": ["Whitespace only lines"]}'
        return "{}"

# Define specialized agents

class TriageAgent(UnifiedAgent):
    def __init__(self):
        super().__init__(
            role="Triage Agent",
            instructions="You extract key symptoms, expected vs actual behavior, environment details, and prioritize hypotheses from a bug report and logs."
        )

    def run(self, bug_report: str, logs: str) -> str:
        prompt = f"Bug Report:\n{bug_report}\n\nLogs:\n{logs}\n\nExtract the requested triage information."
        return self._execute(prompt, schema=TriageResult)

class LogAnalystAgent(UnifiedAgent):
    def __init__(self):
         super().__init__(
            role="Log Analyst Agent",
            instructions="You search logs for stack traces, error signatures, frequency, correlation with deploy/version, and key anomalies."
        )

    def run(self, logs: str, triage_context: str) -> str:
        prompt = f"Analyze these logs and extract anomalies. Context: {triage_context}\nLogs: {logs}"
        return self._execute(prompt, schema=LogAnalysisResult)

class ReproductionAgent(UnifiedAgent):
    def __init__(self):
        super().__init__(
            role="Reproduction Agent",
            instructions="You construct a minimal reproduction script/test and run it using tools to confirm the bug exists."
        )

    def run(self, triage_context: str, repo_path: str) -> str:
        agent_tools = [tools.search_files, tools.read_file, tools.write_test_script, tools.run_test_script]
        prompt = f"Context: {triage_context}\nRepo path is: {repo_path}\nYou MUST create a minimal python repro script to reproduce the bug exactly, write it to 'repro.py', and run it. Return a JSON formatted as ReproductionResult schema."
        return self._execute(prompt, schema=ReproductionResult, available_tools=agent_tools, context=triage_context)

class FixPlannerAgent(UnifiedAgent):
    def __init__(self):
        super().__init__(
            role="Fix Planner Agent",
            instructions="You propose a root-cause hypothesis, patch approach, and verification plan based on repro outcome and log evidence."
        )

    def run(self, repo_path: str, repro_outcome: str, log_analysis: str) -> str:
         agent_tools = [tools.read_file, tools.search_files]
         prompt = f"Repro Outcome: {repro_outcome}\nLog Analysis: {log_analysis}\nRepo Path: {repo_path}\nProvide a patch plan using the provided schema."
         return self._execute(prompt, schema=FixPlanResult, available_tools=agent_tools)

class ReviewerAgent(UnifiedAgent):
    def __init__(self):
        super().__init__(
            role="Reviewer/Critic Agent",
            instructions="You challenge weak assumptions, check whether the repro is truly minimal, verify the fix plan is safe, and suggest edge cases."
        )
        
    def run(self, fix_plan: str, repro_outcome: str) -> str:
        prompt = f"Fix Plan:\n{fix_plan}\nRepro Outcome:\n{repro_outcome}\nReview the plan and approve or reject."
        return self._execute(prompt, schema=ReviewResult)
