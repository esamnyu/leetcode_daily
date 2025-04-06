import subprocess
import os
import datetime
import sys
import time

# --- Configuration ---
PROBLEMS_DIR = "problems"
GIT_BRANCH = "main" # Change if you use a different branch name
# --- End Configuration ---

def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print("Output:\n", result.stdout)
        if result.stderr:
            print("Error output:\n", result.stderr, file=sys.stderr)
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}. Is git installed and in PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        print(f"Output: {e.stdout}", file=sys.stderr)
        print(f"Error Output: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

# 1. Find the most recently modified python file in problems/
#    (Or rely on git status if the start script didn't commit everything)
print("--- Detecting Modified Problem File ---")
problem_file = None

# Check git status first for modified files not yet staged
git_status_output = run_command(["git", "status", "--porcelain", PROBLEMS_DIR])
modified_files = []
for line in git_status_output.splitlines():
    status = line[:2].strip()
    filepath = line[3:]
    if filepath.startswith(PROBLEMS_DIR + os.path.sep) and filepath.endswith(".py"):
       if status == 'M':
           modified_files.append(filepath)

if modified_files:
     if len(modified_files) > 1:
          print(f"Warning: Multiple modified files detected: {modified_files}. Using the first one: {modified_files[0]}", file=sys.stderr)
     problem_file = modified_files[0]
     print(f"Detected modified file via git status: {problem_file}")
else:
    # If git status shows nothing, find the most recently touched file (less reliable)
    print("No modified files in git status, checking file modification times...")
    try:
        latest_time = 0
        for filename in os.listdir(PROBLEMS_DIR):
            if filename.endswith(".py"):
                filepath = os.path.join(PROBLEMS_DIR, filename)
                mod_time = os.path.getmtime(filepath)
                if mod_time > latest_time:
                    latest_time = mod_time
                    problem_file = filepath
        if problem_file:
             print(f"Detected most recently modified file: {problem_file}")
        else:
             print(f"Error: Could not find a Python file to commit in {PROBLEMS_DIR}", file=sys.stderr)
             sys.exit(1)
    except FileNotFoundError:
         print(f"Error: Problems directory '{PROBLEMS_DIR}' not found.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        print(f"Error finding file by modification time: {e}", file=sys.stderr)
        sys.exit(1)

print("-" * 30)

# 2. Stage the file
print("--- Staging File ---")
run_command(["git", "add", problem_file])
print("-" * 30)

# 3. Commit the completed file
print("--- Committing Final Version ---")
today_date = datetime.date.today().strftime("%Y-%m-%d")
# Check if there are staged changes before committing
staged_changes = run_command(["git", "diff", "--staged", "--name-only"])
if not staged_changes:
    print("No changes staged for commit. Did you save your solution?", file=sys.stderr)
    # Optional: Exit or proceed to push anyway
    # sys.exit(1) 
    print("Proceeding to push existing commits...")
else:
    commit_message = f"feat: Complete LeetCode daily challenge {today_date}"
    run_command(["git", "commit", "-m", commit_message])
print("-" * 30)


# 4. Push to GitHub
print("--- Pushing to GitHub ---")
run_command(["git", "push", "origin", GIT_BRANCH])
print("-" * 30)

print("\n✅ Final commit and push done for the day!")