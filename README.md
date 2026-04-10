# AI Bug Report Multi-Agent System

This project is an automated bug investigation system that orchestrates multiple autonomous AI agents to ingest bug reports, analyze stack traces, dynamically write Reproduction scripts via executing python locally, and propose root-cause fixes.

## Tech Stack

* **Python 3.9+**: Core system language.
* **LLM Integration**: Uses the `openai` Python client to interface with LLMs (currently configured for a local Ollama instance with `llama3.2`, but adaptable to OpenAI endpoints or Gemini through its compatibility API).
* **Pydantic**: Enforces strict structured JSON schema outputs from the Agents.
* **python-dotenv**: Manages configuration and environment variables.
* **Local Tool Environment**: A sandboxed execution environment built using Python's `subprocess` and `os` modules to provide programatic file operations and run reproduction scripts locally.

## Project Structure

```text
ai-bug-report/
├── .env                    # Environment variables (create from .env.template)
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── main.py                 # CLI entry point to run the system
├── final_report.json       # Generated output from the multi-agent pipeline
├── repo/                   # Target repository where the bug resides
│   └── (source files)
├── inputs/                 # Initial input files for the run
│   ├── bug_report.md       # User-provided bug description
│   └── error_logs.txt      # Attached stack traces or server logs
└── system/
    ├── __init__.py
    ├── agents.py           # Defines UnifiedAgent and subclassed specialized agents
    ├── models.py           # Pydantic schemas for structured JSON output
    ├── orchestrator.py     # State machine running the agents in sequence
    └── tools.py            # Local python tools (read, write, search, run)
```

## Setup and Run Instructions

### 1. Prerequisites
* Python 3.9+ installed
* A local LLM runner such as Ollama running on `http://localhost:11434` (or you can reconfigure the base URL and API keys in the code).

### 2. Environment Setup
Creating a virtual environment is highly recommended.

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Application Configuration
Copy the `.env.template` file to `.env` to set up your environment variables (like API keys or base URLs, if you adjust the agent configuration).
```bash
cp .env.template .env
```
Ensure your target model instance is active locally so that the agents are reachable.

### 4. Running the System
Use the `main.py` CLI to trigger the multi-agent orchestration. You must provide the target repository path, the bug report file, and the corresponding log file.

```bash
python main.py --repo repo --report inputs/bug_report.md --logs inputs/error_logs.txt
```

If successful, the system's aggregated findings will be saved to `final_report.json` in the root directory.

## The Agents

The system passes context through five specialized autonomous agents:

1. **Triage Agent**: Extracts key symptoms, expected vs. actual behavior, and environment details. It prioritizes initial hypotheses purely from reading the bug report and logs.
2. **Log Analyst Agent**: Searches logs for stack traces, error signatures, frequency, and correlation with deployments. It identifies anomalous patterns to narrow down the domain of the root cause.
3. **Reproduction Agent**: The action-oriented agent. Provided with programmatic tools via `system/tools.py`, it constructs a minimal python repro script, writes it to the local file system (`repro.py`), and executes it to safely confirm the bug exists exactly as reported.
4. **Fix Planner Agent**: Analyzes the log evidence together with the output from the Reproduction Agent. It proposes a firm root-cause hypothesis, formulates a patch approach, identifies the implicated files, and specifies a verification plan.
5. **Reviewer Agent**: Acts as the devil's advocate. It challenges weak assumptions, verifies that the proposed plan is fundamentally safe, confirms the isolation of the reproduction script, and flags edge cases.

## Workflow

1. **Initialization**: The user invokes `main.py` which reads the inputs from disk and spins up the `SystemOrchestrator`.
2. **Sequential Hand-off**: Context is piped sequentially from one agent's resolution to the next: `Triage -> Log Analyst -> Reproduction -> Fix Planner -> Reviewer`.
3. **Tool Loop Execution**: When tool-enabled agents (like the Reproduction Agent) generate function call requests, the Orchestrator intercepts them. It leverages local Python implementations (`read_file`, `search_files`, `write_test_script`, `run_test_script`) and injects the output back into the LLM's prompt history.
4. **Structured Generation**: `pydantic` schemas instruct the LLMs to yield highly predictable JSON. A mock failover gracefully outputs pre-determined dummy data on API timeout or error ensuring pipeline continuity.
5. **Reporting**: Ultimately, the orchestrator stitches the states of all agent schemas together, summarizing them into the final structured `final_report.json` output.

## System Architecture

```mermaid
graph TD
    A[User Inputs] -->|CLI Args| B[main.py CLI]
    B -->|Instantiates| C(Orchestrator)
    
    C -->|Context| D[1. Triage Agent]
    D -->|TriageResult JSON| C
    
    C -->|Context| E[2. Log Analyst Agent]
    E -->|LogAnalysisResult JSON| C
    
    C -->|Context| F[3. Reproduction Agent]
    F <-->|Tool Execution Loop| G[(Local File System / Shell)]
    F -->|ReproductionResult JSON| C
    
    C -->|Context| H[4. Fix Planner Agent]
    H -->|FixPlanResult JSON| C
    
    C -->|Context| I[5. Reviewer Agent]
    I -->|ReviewResult JSON| C
    
    C -->|Assembles Output| J{final_report.json}
```
