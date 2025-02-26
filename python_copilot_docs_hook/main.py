#!/usr/bin/env python3
import logging
import os
import ast
import argparse
import subprocess
import tempfile
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('python_copilot_docs_hook')

def get_copilot_suggestion(code: str) -> str:
    """Get documentation suggestion using GitHub Copilot CLI."""
    try:
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp:
            temp.write(code)
            temp_path = temp.name

        # Try suggest command first
        try:
            result = subprocess.run(
                ['gh', 'copilot', 'suggest', '-t', 'python'],
                input=f"Generate Python docstring for:\n{code}",
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                return format_suggestion(result.stdout)
        except subprocess.CalledProcessError:
            logger.debug("Suggest command failed, trying explain command")

        # Fallback to explain command
        result = subprocess.run(
            ['gh', 'copilot', 'explain'],
            input=code,
            capture_output=True,
            text=True,
            check=True
        )

        # Clean up temp file
        os.unlink(temp_path)

        return format_suggestion(result.stdout) if result.stdout else ""

    except Exception as e:
        logger.error(f"Error getting Copilot suggestion: {e}")
        return ""

def format_suggestion(text: str) -> str:
    """Format Copilot output as a proper docstring."""
    lines = []
    paragraphs = text.split('\n\n')

    # Extract main description
    if paragraphs:
        desc = paragraphs[0].strip()
        if 'This code' in desc or 'The function' in desc:
            desc = desc.split('.')[0].strip()
        lines.append(desc)
        lines.append("")

    # Process parameters
    for para in paragraphs:
        if "Parameters:" in para or "Args:" in para:
            lines.append("Args:")
            for line in para.split('\n')[1:]:
                if ':' in line:
                    param, desc = line.split(':', 1)
                    lines.append(f"    {param.strip()}: {desc.strip()}")
                elif line.strip():
                    lines.append(f"    {line.strip()}")
            lines.append("")

    # Process return value
    for para in paragraphs:
        if "Returns:" in para:
            lines.append("Returns:")
            ret_desc = para.split('Returns:', 1)[1].strip()
            lines.append(f"    {ret_desc}")
            lines.append("")

    return "\n".join(lines).strip()

def update_file_with_docs(filename: str) -> bool:
    """Update Python file with generated documentation."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.error(f"Syntax error in file: {filename}")
        return False

    modified = False

    # Generate module docstring if missing
    if not ast.get_docstring(tree):
        logger.debug("Generating module docstring")
        module_doc = get_copilot_suggestion(content)
        if module_doc:
            content = f'"""{module_doc}"""\n\n{content}'
            modified = True

    # Find and generate function docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
            logger.debug(f"Generating docstring for function: {node.name}")
            func_code = ast.get_source_segment(content, node)
            doc = get_copilot_suggestion(func_code)
            
            if doc:
                # Insert docstring after function definition
                lines = content.splitlines()
                indent = ' ' * node.col_offset
                doc_lines = [f'{indent}    """{line}"""' for line in doc.splitlines()]
                lines.insert(node.lineno, '\n'.join(doc_lines))
                content = '\n'.join(lines)
                modified = True

    # Write changes if any modifications were made
    if modified:
        logger.info(f"Updating file with generated documentation: {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

    return True

def main() -> int:
    """Process Python files and add missing documentation."""
    parser = argparse.ArgumentParser(
        description='Add missing documentation to Python files using GitHub Copilot'
    )
    parser.add_argument('filenames', nargs='*', help='Python files to process')
    args = parser.parse_args()

    try:
        # Check if gh CLI and Copilot extension are available
        try:
            subprocess.run(['gh', '--version'], check=True, capture_output=True)
            subprocess.run(['gh', 'copilot', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("GitHub CLI or Copilot extension not found. Please install:")
            logger.error("1. brew install gh")
            logger.error("2. gh extension install github/gh-copilot")
            logger.error("3. gh auth login")
            return 1

        # Process each Python file
        exit_code = 0
        for filename in args.filenames:
            if filename.endswith('.py'):
                logger.debug(f"Processing file: {filename}")
                if not update_file_with_docs(filename):
                    exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())