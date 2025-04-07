import subprocess
import os
import datetime
import sys

# --- Configuration ---
PROBLEMS_DIR = "problems"
SCRIPTS_DIR = "scripts"
GIT_REMOTE = "origin" # Change if your remote is named differently
GIT_BRANCH = "main" # Change if you use a different branch name
# --- End Configuration ---

def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        print(f"Running: {' '.join(command)}")
        # Use check=False for git diff --quiet as non-zero is expected
        check_flag = True
        if command[0:3] == ['git', 'diff', '--cached']:
             check_flag = False # Allow non-zero exit for diff check

        result = subprocess.run(command, check=check_flag, capture_output=True, text=True, encoding='utf-8')

        # Print stdout only if it's not empty
        if result.stdout:
             print("Output:\n", result.stdout.strip())
        # Print stderr only if it's not empty and not expected git push progress
        if result.stderr:
            stderr_lower = result.stderr.lower()
            # Filter out common git push progress messages
            if not (command[0:2] == ['git', 'push'] and ('enumerating objects' in stderr_lower or 'counting objects' in stderr_lower or 'compressing objects' in stderr_lower or 'writing objects' in stderr_lower or 'to github.com' in stderr_lower)):
                 print("Error output:\n", result.stderr.strip(), file=sys.stderr)

        # Return specific result for git diff check if needed later
        if command[0:3] == ['git', 'diff', '--cached']:
             return result # Return the full CompletedProcess object

        return result.stdout.strip()
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}. Is git installed and in PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # This block might not be reached for git diff if check=False,
        # but keep it for other commands or unexpected diff errors.
        print(f"Error running command: {' '.join(command)}", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        if e.stdout:
             print(f"Output: {e.stdout.strip()}", file=sys.stderr)
        if e.stderr:
             print(f"Error Output: {e.stderr.strip()}", file=sys.stderr)
        # Exit unless it's the specific git diff check that failed as expected
        if not (command[0:3] == ['git', 'diff', '--cached'] and e.returncode == 1):
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
    filepath = line[3:].strip() # Strip whitespace just in case
    # Ensure the path processing handles potential spaces in filenames correctly if needed
    if filepath.startswith(PROBLEMS_DIR + os.path.sep) and filepath.endswith(".py"):
       if status == '??' or status == 'M':
           new_or_modified_files.append(filepath)

problem_file = None # Initialize
if not new_or_modified_files:
    print("Warning: No new or modified Python problem file detected via git status in", PROBLEMS_DIR, file=sys.stderr)
    # Fallback: Check filesystem for the newest .py file in the directory
    # This is less reliable but might catch files generated but not yet seen by git status (unlikely but possible)
    try:
        py_files = [os.path.join(PROBLEMS_DIR, f) for f in os.listdir(PROBLEMS_DIR) if f.endswith(".py")]
        if py_files:
             latest_file = max(py_files, key=os.path.getmtime)
             print(f"Falling back to newest file by mod time: {latest_file}")
             new_or_modified_files.append(latest_file)
             # If we use filesystem fallback, ensure git knows about it if it was untracked
             run_command(["git", "add", latest_file])
        else:
             print("Error: Could not determine the relevant problem file via git status or filesystem.", file=sys.stderr)
             sys.exit(1)
    except FileNotFoundError:
         print(f"Error: Problems directory '{PROBLEMS_DIR}' not found during fallback check.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
         print(f"Error during filesystem fallback check: {e}", file=sys.stderr)
         sys.exit(1)


# Assuming the generate script creates/modifies only one relevant file per run
if len(new_or_modified_files) > 1:
     # Filter out potential .gitkeep if we used filesystem check
     new_or_modified_files = [f for f in new_or_modified_files if os.path.basename(f) != '.gitkeep']
     if len(new_or_modified_files) > 1:
       print(f"Warning: Multiple relevant files detected: {new_or_modified_files}. Using the first one: {new_or_modified_files[0]}", file=sys.stderr)
     elif not new_or_modified_files:
        print("Error: No files detected after filtering.", file=sys.stderr)
        sys.exit(1)

problem_file = new_or_modified_files[0]
print(f"Detected problem file: {problem_file}")
print("-" * 30)


# 3. Stage the file (might be redundant if fallback already added it)
print("--- Staging File ---")
run_command(["git", "add", problem_file])
print("-" * 30)

# 4. Commit the initial file
print("--- Committing Initial Version ---")
# Check if there are staged changes before committing
diff_result = run_command(["git", "diff", "--cached", "--quiet"])
# git diff --quiet exits with 1 if there are changes, 0 if none.
if diff_result.returncode == 1:
    print("Staged changes detected, proceeding with commit.")
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    # Extract problem title for commit message if possible
    problem_title_part = "Unknown Problem"
    try:
        # Basic extraction, assumes format YYYY-MM-DD_NNNN_problem-name.py
        base_name = os.path.basename(problem_file)
        parts = base_name.split('_', 2)
        if len(parts) >= 3:
             title_slug = parts[2].replace(".py", "")
             problem_title_part = title_slug.replace("-", " ").capitalize()
        else: # Fallback if filename format is unexpected
             problem_title_part = base_name.replace(".py", "").replace("_", " ")

    except Exception:
        pass # Ignore errors during title extraction, use default

    commit_message = f"feat: Start LeetCode {problem_title_part} ({today_date})"
    run_command(["git", "commit", "-m", commit_message])
elif diff_result.returncode == 0:
    print("Warning: No changes staged for commit. Skipping commit and push.", file=sys.stderr)
    # Exit gracefully if no changes - maybe the file existed and was identical
    print("\n✅ No changes detected. Exiting.")
    sys.exit(0)
else:
    # Unexpected return code from git diff
    print(f"Error: Unexpected return code {diff_result.returncode} from 'git diff --cached --quiet'.", file=sys.stderr)
    sys.exit(1)

print("-" * 30)

# 5. Push the commit to the remote repository
print(f"--- Pushing to Remote ({GIT_REMOTE}/{GIT_BRANCH}) ---")
run_command(["git", "push", GIT_REMOTE, GIT_BRANCH])
print("-" * 30)

print(f"\n✅ Initial commit for {problem_title_part} created and pushed successfully!")
print(f"   File: {problem_file}")
# Message about scheduling removed as it's handled by the workflow context
