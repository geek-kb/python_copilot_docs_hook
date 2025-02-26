#!/usr/bin/env python3
import logging
import os
import ast
import argparse
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('python_copilot_docs_hook')

def check_docstrings(filename: str) -> Dict[str, List[int]]:
    """Check for missing docstrings in Python file."""
    missing_docs = {'module': [], 'functions': []}

    with open(filename, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            logger.error(f"Syntax error in file: {filename}")
            return missing_docs

    # Check module docstring
    if not ast.get_docstring(tree):
        missing_docs['module'].append(1)
        logger.info(f"Module docstring missing in {filename}")

    # Check function docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                missing_docs['functions'].append(node.lineno)
                logger.info(f"Function docstring missing for '{node.name}' at line {node.lineno}")

    return missing_docs

def generate_report(filename: str, missing_docs: Dict[str, List[int]]) -> str:
    """Generate report for missing documentation."""
    report = []

    if missing_docs['module'] or missing_docs['functions']:
        report.append(f"\nMissing documentation in {filename}:")

        if missing_docs['module']:
            report.append("- Module docstring missing")
            report.append("  Suggestion: Place cursor at line 1 and press Alt+\\")

        if missing_docs['functions']:
            report.append("- Function docstrings missing at lines: " +
                        ", ".join(map(str, missing_docs['functions'])))
            report.append("  Suggestion: Place cursor at function definition and press Alt+\\")

    return "\n".join(report)

def main() -> int:
    """Process Python files and check for missing documentation."""
    parser = argparse.ArgumentParser(
        description='Check Python files for missing documentation'
    )
    parser.add_argument('filenames', nargs='*', help='Python files to check')
    args = parser.parse_args()

    try:
        exit_code = 0

        for filename in args.filenames:
            if filename.endswith('.py'):
                logger.debug(f"Checking {filename}")
                missing_docs = check_docstrings(filename)

                if missing_docs['module'] or missing_docs['functions']:
                    print(generate_report(filename, missing_docs))
                    exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())
