import subprocess
import os
import datetime
import sys

# --- Configuration ---
PROBLEMS_DIR = "problems"
SCRIPTS_DIR = "scripts"
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

# 1. Generate the challenge
print("--- Generating Daily Challenge ---")
generate_script_path = os.path.join(SCRIPTS_DIR, "generate_challenge.py")
# Ensure we run python from the environment where dependencies are installed
run_command([sys.executable, generate_script_path]) 
print("-" * 30)

# 2. Find the newly added/modified problem file
print("--- Detecting Problem File ---")
# Get status - look for untracked ('??') or modified (' M') python files in problems/
git_status_output = run_command(["git", "status", "--porcelain", PROBLEMS_DIR])
new_or_modified_files = []
for line in git_status_output.splitlines():
    status = line[:2].strip()
    filepath = line[3:]
    if filepath.startswith(PROBLEMS_DIR + os.path.sep) and filepath.endswith(".py"):
       if status == '??' or status == 'M':
           new_or_modified_files.append(filepath)

if not new_or_modified_files:
    print("Error: No new or modified Python problem file detected in", PROBLEMS_DIR, file=sys.stderr)
    # Attempt to find the most recently *committed* file if generation modified an existing one
    # This part might need refinement based on how generate_challenge.py behaves exactly
    print("Checking last commit for relevant file...")
    try:
        last_commit_file = run_command(["git", "log", "-1", "--name-only", "--pretty=format:", "--", PROBLEMS_DIR + "/*.py"]).strip()
        if last_commit_file and last_commit_file.endswith(".py"):
             print(f"Assuming modification of last committed file: {last_commit_file}")
             new_or_modified_files.append(last_commit_file)
        else:
             print("Could not determine the relevant problem file.", file=sys.stderr)
             sys.exit(1)

    except Exception as e:
         print(f"Error checking last commit: {e}", file=sys.stderr)
         sys.exit(1)


# Assuming the generate script creates/modifies only one relevant file per run
if len(new_or_modified_files) > 1:
     print(f"Warning: Multiple files detected: {new_or_modified_files}. Using the first one: {new_or_modified_files[0]}", file=sys.stderr)

problem_file = new_or_modified_files[0]
print(f"Detected problem file: {problem_file}")
print("-" * 30)


# 3. Stage the file
print("--- Staging File ---")
run_command(["git", "add", problem_file])
print("-" * 30)

# 4. Commit the initial file
print("--- Committing Initial Version ---")
today_date = datetime.date.today().strftime("%Y-%m-%d")
commit_message = f"feat: Start LeetCode daily challenge {today_date}"
run_command(["git", "commit", "-m", commit_message])
print("-" * 30)

print("\n✅ Initial commit done. The problem file is ready for you to solve!")
print(f"   File: {problem_file}")
print("\nRun 'python finish_day.py' after you solve it.")