import json
import os
from .agents import TriageAgent, LogAnalystAgent, ReproductionAgent, FixPlannerAgent, ReviewerAgent

class SystemOrchestrator:
    def __init__(self, repo_path: str, bug_report_path: str, logs_path: str):
        self.repo_path = repo_path
        self.bug_report_path = bug_report_path
        self.logs_path = logs_path
        self.state = {}
        
    def _read_input(self, path: str) -> str:
        try:
             with open(path, 'r', encoding='utf-8') as f:
                 return f.read()
        except Exception as e:
             return f"Error reading {path}: {e}"
             
    def run(self):
        print("====== AI BUG REPORT ORCHESTRATOR STARTING ======")
        bug_report = self._read_input(self.bug_report_path)
        logs = self._read_input(self.logs_path)
        
        print("\n--- [1] TRIAGE AGENT ---")
        triage_agent = TriageAgent()
        triage_res = triage_agent.run(bug_report, logs)
        self.state['triage'] = json.loads(triage_res) if isinstance(triage_res, str) else triage_res
        print("Triage OK.")
        
        print("\n--- [2] LOG ANALYST AGENT ---")
        log_agent = LogAnalystAgent()
        log_res = log_agent.run(logs, json.dumps(self.state['triage']))
        self.state['log_analysis'] = json.loads(log_res) if isinstance(log_res, str) else log_res
        print("Log Analysis OK.")
        
        print("\n--- [3] REPRODUCTION AGENT ---")
        repro_agent = ReproductionAgent()
        repro_res = repro_agent.run(json.dumps(self.state['triage']), self.repo_path)
        # Check if the result is already a dict (mocked) or JSON string
        try:
           self.state['reproduction'] = json.loads(repro_res) if isinstance(repro_res, str) else repro_res
        except Exception as e:
           print(f"Warning: Repro agent did not return valid JSON. Error: {e}")
           self.state['reproduction'] = {"raw_output": repro_res}
        print("Reproduction OK.")
        
        print("\n--- [4] FIX PLANNER AGENT ---")
        fix_agent = FixPlannerAgent()
        fix_res = fix_agent.run(self.repo_path, json.dumps(self.state['reproduction']), json.dumps(self.state['log_analysis']))
        try:
            self.state['fix_plan'] = json.loads(fix_res) if isinstance(fix_res, str) else fix_res
        except Exception as e:
            self.state['fix_plan'] = {"raw_output": fix_res}
        print("Fix Plan OK.")
        
        print("\n--- [5] REVIEWER AGENT ---")
        review_agent = ReviewerAgent()
        review_res = review_agent.run(json.dumps(self.state['fix_plan']), json.dumps(self.state['reproduction']))
        try:
            self.state['review'] = json.loads(review_res) if isinstance(review_res, str) else review_res
        except Exception as e:
            self.state['review'] = {"raw_output": review_res}
        print("Review OK.")
        
        print("\n--- [6] PREPARING FINAL REPORT ---")
        final_report = {
            "bug_summary": self.state.get("triage", {}),
            "evidence": self.state.get("log_analysis", {}),
            "reproduction": self.state.get("reproduction", {}),
            "root_cause": self.state.get("fix_plan", {}).get("root_cause_hypothesis", "Unknown"),
            "confidence": self.state.get("fix_plan", {}).get("confidence", "Unknown"),
            "patch_plan": {
                 "approach": self.state.get("fix_plan", {}).get("patch_approach", ""),
                 "impacted_files": self.state.get("fix_plan", {}).get("impacted_files", [])
            },
            "validation_plan": self.state.get("fix_plan", {}).get("verification_plan", ""),
            "open_questions": self.state.get("review", {}).get("edge_cases", [])
        }
        
        output_path = "final_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4)
        print(f"Final report written to {output_path}")
        return final_report
