import subprocess
import os

def read_file(file_path: str) -> str:
    """Reads a file and returns its content. Used to inspect logs, reports, or code."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def search_files(directory: str, query: str) -> str:
    """Searches for a regex query in files within the given directory (like ripgrep)."""
    # A simple custom implementation instead of requiring ripgrep installed
    results = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if query in line:
                                results.append(f"{filepath}:{i+1}:{line.strip()}")
                except:
                    pass
        if not results:
            return "No matches found."
        return "\n".join(results)
    except Exception as e:
         return f"Error searching: {e}"

def write_test_script(script_path: str, code: str) -> str:
    """Writes Python code to a specific file path."""
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return f"Script written successfully to {script_path}"
    except Exception as e:
        return f"Error writing script: {e}"

def run_test_script(script_path: str, args: str = "") -> str:
    """Runs a Python script and returns standard output and error."""
    try:
        cmd = f"python {script_path} {args}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        return f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}\n--- EXIT CODE ---\n{result.returncode}"
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out."
    except Exception as e:
        return f"Error running script: {e}"
