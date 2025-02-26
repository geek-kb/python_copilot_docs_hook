#!/usr/bin/env python3
"""Python documentation generator using GitHub Copilot CLI."""

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
        # Try with specific Python docstring prompt
        result = subprocess.run(
            ['gh', 'copilot', 'suggest'],
            input=(
                "Generate a Python docstring with Args, Returns, and Raises sections "
                f"for this code:\n\n{code}\n\n"
                "Format: Google-style docstring with Args/Returns/Raises sections"
            ),
            text=True,
            capture_output=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout:
            suggestion = result.stdout.strip()
            # Clean up Copilot's response
            if suggestion.startswith('"""') and suggestion.endswith('"""'):
                suggestion = suggestion[3:-3].strip()
            return format_suggestion(suggestion)

        logger.debug(f"Suggest command failed: {result.stderr}")

        # Try with explain command as fallback
        result = subprocess.run(
            ['gh', 'copilot', 'explain'],
            input=code,
            text=True,
            capture_output=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout:
            return format_suggestion(result.stdout)

        logger.error("All Copilot commands failed")
        return ""

    except subprocess.TimeoutExpired:
        logger.error("Copilot command timed out after 15 seconds")
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

    # Process exceptions
    for para in paragraphs:
        if "Raises:" in para:
            lines.append("Raises:")
            for line in para.split('\n')[1:]:
                if ':' in line:
                    exc, desc = line.split(':', 1)
                    lines.append(f"    {exc.strip()}: {desc.strip()}")
                elif line.strip():
                    lines.append(f"    {line.strip()}")
            lines.append("")

    return "\n".join(lines).strip()

def validate_file(filename: str) -> bool:
    """Validate Python file before processing."""
    if not os.path.isfile(filename):
        logger.error(f"File not found: {filename}")
        return False
        
    if not filename.endswith('.py'):
        logger.error(f"Not a Python file: {filename}")
        return False
        
    return True

def update_file_with_docs(filename: str) -> bool:
    """Update Python file with generated documentation."""
    if not validate_file(filename):
        return False

    try:
        # Read file content
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Parse Python code
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            lines = content.splitlines()
            if 0 <= e.lineno - 1 < len(lines):
                problematic_line = lines[e.lineno - 1]
                logger.error(f"Syntax error in file {filename}:")
                logger.error(f"Line {e.lineno}: {problematic_line}")
                logger.error(f"Error: {e.msg}")
                logger.error(" " * (e.offset + 7) + "^")
            else:
                logger.error(f"Syntax error in file {filename} at line {e.lineno}: {e.msg}")
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
                    lines = content.splitlines()
                    indent = ' ' * node.col_offset
                    doc_lines = [f'{indent}    """{line}"""' for line in doc.splitlines()]
                    lines.insert(node.lineno, '\n'.join(doc_lines))
                    content = '\n'.join(lines)
                    modified = True

        # Write changes if modified
        if modified:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Updated documentation in {filename}")

        return True

    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        return False

def main() -> int:
    """Process Python files and add missing documentation."""
    parser = argparse.ArgumentParser(
        description='Add missing documentation to Python files using GitHub Copilot'
    )
    parser.add_argument('filenames', nargs='*', help='Python files to process')
    args = parser.parse_args()

    try:
        # Verify GitHub CLI and Copilot extension
        try:
            subprocess.run(['gh', '--version'], check=True, capture_output=True)
            subprocess.run(['gh', 'copilot', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("GitHub CLI or Copilot extension not found. Please install:")
            logger.error("1. brew install gh")
            logger.error("2. gh extension install github/gh-copilot")
            logger.error("3. gh auth login")
            return 1

        # Process files
        exit_code = 0
        for filename in args.filenames:
            logger.debug(f"Processing file: {filename}")
            if not update_file_with_docs(filename):
                exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())