import os
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json

# Configuration
LEETCODE_API_URL = "https://leetcode.com/api/problems/all/"
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
PROBLEM_URL_TEMPLATE = "https://leetcode.com/problems/{}/description/"

def get_random_problem():
    """Fetch a random problem from LeetCode's API."""
    try:
        response = requests.get(LEETCODE_API_URL)
        response.raise_for_status()  # Raise exception for HTTP errors
        problems = response.json()['stat_status_pairs']
        
        # Filter for problems that aren't premium and have reasonable difficulty
        eligible_problems = [p for p in problems if not p['paid_only'] and p['difficulty']['level'] <= 2]
        
        if not eligible_problems:
            print("No eligible problems found. Check API response.")
            return None
            
        problem = random.choice(eligible_problems)
        
        return {
            'title_slug': problem['stat']['question__title_slug'],
            'frontend_id': problem['stat']['frontend_question_id'],
            'difficulty': problem['difficulty']['level']
        }
    except Exception as e:
        print(f"Error fetching random problem: {e}")
        return None

def get_problem_details_graphql(title_slug):
    """Fetch problem description and code template using GraphQL API."""
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        content
        difficulty
        codeSnippets {
          lang
          langSlug
          code
        }
        topicTags {
          name
        }
      }
    }
    """
    
    try:
        response = requests.post(
            LEETCODE_GRAPHQL_URL,
            json={'query': query, 'variables': {'titleSlug': title_slug}},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL errors: {data['errors']}")
            return None
            
        question = data['data']['question']
        
        # Find Python code snippet
        python_snippet = None
        for snippet in question['codeSnippets']:
            if snippet['langSlug'] == 'python3' or snippet['langSlug'] == 'python':
                python_snippet = snippet['code']
                break
                
        if not python_snippet:
            python_snippet = "# No Python template available\n\n# Implement your solution here\n"
        
        # Create a simplified template by replacing solution logic with placeholders
        template_lines = python_snippet.split('\n')
        simplified_template = []
        in_method_body = False
        
        for line in template_lines:
            # Always keep import statements, class definitions, and method signatures
            if line.strip().startswith(('import', 'from', 'class ', 'def ')):
                simplified_template.append(line)
                if line.strip().endswith(':'):
                    in_method_body = True
            # Keep structural parts like return statements but simplify logic
            elif 'return' in line:
                indentation = len(line) - len(line.lstrip())
                simplified_template.append(' ' * indentation + 'return None  # TODO: Implement your solution')
                in_method_body = False
            # For method bodies, add a placeholder
            elif in_method_body and line.strip() and not line.strip().startswith('#'):
                # If we encounter the first line of method body, add placeholder
                indentation = len(line) - len(line.lstrip())
                simplified_template.append(' ' * indentation + '# TODO: Implement your solution here')
                simplified_template.append(' ' * indentation + 'pass')
                in_method_body = False  # Don't add more placeholders for this method
            # Keep any other structural elements
            elif not line.strip() or line.strip().startswith('#') or not in_method_body:
                simplified_template.append(line)
                
        return {
            'title': question['title'],
            'description': BeautifulSoup(question['content'], 'html.parser').get_text(),
            'difficulty': question['difficulty'],
            'template': '\n'.join(simplified_template),
            'topics': [tag['name'] for tag in question['topicTags']]
        }
    except Exception as e:
        print(f"Error fetching problem details via GraphQL: {e}")
        return None

def get_problem_details_web(title_slug):
    """Fallback method to fetch problem details via web scraping if GraphQL fails."""
    url = PROBLEM_URL_TEMPLATE.format(title_slug)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract problem description - this selector might need adjustment based on LeetCode's current HTML structure
        description_div = soup.select_one('div[class*="description"]')
        description = description_div.get_text() if description_div else "Description not available"
        
        # Extract title
        title_element = soup.select_one('div[class*="title"]')
        title = title_element.get_text() if title_element else "Title not available"
        
        # Create a basic template since extracting code is challenging via scraping
        template = (
            "# LeetCode template\n\n"
            "class Solution:\n"
            "    def solve(self):\n"
            "        # TODO: Implement your solution here\n"
            "        pass\n"
        )
        
        return {
            'title': title,
            'description': description,
            'template': template,
            'difficulty': 'Unknown',
            'topics': []
        }
    except Exception as e:
        print(f"Error fetching problem details via web scraping: {e}")
        return {
            'title': 'Problem fetch failed',
            'description': f'Could not retrieve problem details. Error: {e}',
            'template': '# Error fetching problem\n\n# Implement your solution here\n',
            'difficulty': 'Unknown',
            'topics': []
        }

def create_problem_file(problem_data, details):
    """Create a formatted problem file."""
    today = datetime.now().strftime('%Y-%m-%d')
    # Clean up the title for filename
    clean_title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in problem_data['title_slug'])
    file_name = f"{today}_{problem_data['frontend_id']}_{clean_title}.py"
    file_path = os.path.join('problems', file_name)
    
    # Convert difficulty level to text
    difficulty_map = {1: 'Easy', 2: 'Medium', 3: 'Hard', 'Unknown': 'Unknown'}
    difficulty_text = difficulty_map.get(problem_data.get('difficulty', 'Unknown'), 'Unknown')
    
    # Ensure problems directory exists
    os.makedirs('problems', exist_ok=True)
    
    # Format topics as a comma-separated string if available
    topics_text = ', '.join(details.get('topics', [])) if details.get('topics') else 'None'
    
    with open(file_path, 'w') as f:
        f.write(f"# LeetCode {problem_data['frontend_id']}: {details.get('title', problem_data['title_slug'].replace('-', ' ').title())}\n")
        f.write(f"# Date: {today}\n")
        f.write(f"# Difficulty: {difficulty_text}\n")
        f.write(f"# Topics: {topics_text}\n")
        f.write("\n'''\n")
        f.write(details.get('description', 'Description not available'))
        f.write("\n'''\n\n")
        f.write(details.get('template', '# Template not available\n'))
    
    return file_path

def main():
    """Main function to run the script."""
    print("Fetching a random LeetCode problem...")
    
    # Attempt to get a random problem
    problem = get_random_problem()
    if not problem:
        print("Failed to get a random problem. Exiting.")
        return
    
    print(f"Selected problem: #{problem['frontend_id']} - {problem['title_slug']}")
    
    # Try to get problem details using GraphQL first
    print("Fetching problem details...")
    details = get_problem_details_graphql(problem['title_slug'])
    
    # If GraphQL fails, fall back to web scraping
    if not details:
        print("GraphQL fetch failed, falling back to web scraping...")
        details = get_problem_details_web(problem['title_slug'])
    
    # Create the problem file
    print("Creating problem file...")
    file_path = create_problem_file(problem, details)
    
    print(f"Success! Created daily challenge file: {file_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")