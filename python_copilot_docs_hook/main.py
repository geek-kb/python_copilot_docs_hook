import logging
import os
import ast
import argparse
from typing import Dict, List, Optional
import requests
import json

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('python_copilot_docs_hook')

def get_copilot_suggestion(code: str) -> str:
    """Get documentation suggestion using GitHub Copilot CLI."""
    try:
        result = subprocess.run(
            ['gh', 'copilot', 'suggest', '--format', 'json'],
            input=f"Write a Python docstring for:\n{code}",
            text=True,
            capture_output=True,
            check=True
        )
        response = json.loads(result.stdout)
        return response['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Error getting Copilot suggestion: {e}")
        return ""

def update_file_with_docs(filename: str) -> bool:
    """Update Python file with generated documentation."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.error(f"Syntax error in file: {filename}")
        return False

    # Generate module docstring if missing
    if not ast.get_docstring(tree):
        module_doc = get_copilot_suggestion(content)
        if module_doc:
            content = f'"""{module_doc}"""\n\n{content}'

    # Find and generate function docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
            func_code = ast.get_source_segment(content, node)
            doc = get_copilot_suggestion(func_code)
            if doc:
                # Insert docstring after function definition
                lines = content.splitlines()
                indent = ' ' * node.col_offset
                doc_lines = [f'{indent}    """{line}"""' for line in doc.splitlines()]
                lines.insert(node.lineno, '\n'.join(doc_lines))
                content = '\n'.join(lines)

    # Write updated content back to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main() -> int:
    """Process Python files and add missing documentation."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Python files to process')
    args = parser.parse_args()

    try:
        if not os.environ.get('GITHUB_COPILOT_TOKEN'):
            logger.error("GITHUB_COPILOT_TOKEN environment variable not set")
            return 1

        exit_code = 0
        for filename in args.filenames:
            if filename.endswith('.py'):
                logger.debug(f"Processing {filename}")
                if not update_file_with_docs(filename):
                    exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())
