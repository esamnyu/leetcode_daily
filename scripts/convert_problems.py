import json
import os

# Difficulty mapping - we'll assign based on problem ID ranges
# This is a rough estimation, you may want to refine this
def estimate_difficulty(problem_id):
    id_num = int(problem_id)
    if id_num < 200:
        return "Easy"
    elif id_num < 500:
        return "Medium"
    else:
        return "Medium"  # Default to Medium for higher numbers

# Creates a basic Python template for a problem
def create_template(title):
    snake_case_name = title.lower().replace(' ', '_').replace('-', '_')
    return f"""class Solution:
    def {snake_case_name}(self, nums=None):
        # TODO: Implement your solution here
        pass
"""

# Read the input file
with open('paste.txt', 'r') as f:
    content = f.read()

# Ensure it's proper JSON by adding closing entries
if not content.strip().endswith(']'):
    content += ']'
if not content.strip().startswith('['):
    content = '[' + content

# Parse the JSON
problems = json.loads(content)

# Convert to our expected format
converted_problems = []
for problem in problems:
    # Skip incomplete problems
    if 'id' not in problem or 'title' not in problem:
        continue
        
    # Combine question, examples and constraints into description
    description = problem.get('question', '')
    
    # Add examples
    if 'examples' in problem and problem['examples']:
        description += "\n\nExamples:\n"
        for example in problem['examples']:
            if example:  # Skip empty examples
                description += example + "\n"
    
    # Add constraints
    if 'constraints' in problem and problem['constraints']:
        description += "\nConstraints:\n"
        for constraint in problem['constraints']:
            if constraint:  # Skip empty constraints
                description += constraint + "\n"
    
    # Create the new problem object
    new_problem = {
        "id": problem['id'],
        "title": problem['title'],
        "difficulty": estimate_difficulty(problem['id']),
        "description": description,
        "template": create_template(problem['title'])
    }
    
    converted_problems.append(new_problem)

# Write to our database file
output_path = os.path.join('scripts', 'problem_database.json')
with open(output_path, 'w') as f:
    json.dump(converted_problems, f, indent=2)

print(f"Converted {len(converted_problems)} problems to {output_path}")