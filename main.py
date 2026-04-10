import argparse
import sys
from dotenv import load_dotenv
from system.orchestrator import SystemOrchestrator

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Multi-Agent Bug Report System")
    parser.add_argument("--repo", type=str, required=True, help="Path to the repository")
    parser.add_argument("--report", type=str, required=True, help="Path to the bug report")
    parser.add_argument("--logs", type=str, required=True, help="Path to the logs")
    
    args = parser.parse_args()
    
    print(f"Starting analysis with Repo: {args.repo}, Report: {args.report}, Logs: {args.logs}")
    
    orchestrator = SystemOrchestrator(
         repo_path=args.repo,
         bug_report_path=args.report,
         logs_path=args.logs
    )
    
    final_output = orchestrator.run()
    print("Done! View final_report.json for details.")

if __name__ == "__main__":
    main()
