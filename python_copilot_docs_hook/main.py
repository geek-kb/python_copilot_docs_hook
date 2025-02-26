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
        # Try direct suggestion first
        suggestion = _try_copilot_command(
            ['gh', 'copilot', 'suggest'],
            f"Write a Python docstring for this code:\n\n{code}"
        )
        if suggestion:
            return format_suggestion(suggestion)

        # Try explain command
        suggestion = _try_copilot_command(
            ['gh', 'copilot', 'explain'],
            code
        )
        if suggestion:
            return format_suggestion(suggestion)

        # Try completion as last resort
        suggestion = _try_copilot_command(
            ['gh', 'copilot', 'completion'],
            f'"""\nWrite a complete docstring for this Python code:\n{code}\n"""'
        )
        if suggestion:
            return format_suggestion(suggestion)

        return ""

    except Exception as e:
        logger.error(f"Error getting Copilot suggestion: {e}")
        return ""

def _try_copilot_command(command: List[str], input_text: str, additional_args: List[str] = None) -> Optional[str]:
    """Execute a GitHub Copilot CLI command with proper error handling."""
    try:
        cmd = command + (additional_args or [])
        logger.debug(f"Trying command: {' '.join(cmd)}")
        
        # Run command with input through stdin
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        if result.returncode == 0 and result.stdout:
            return result.stdout
        
        if result.stderr:
            logger.debug(f"Command failed: {result.stderr}")
        
        return None
            
    except Exception as e:
        logger.debug(f"Command execution failed: {e}")
        return None
    
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
    try:
        # Read file content
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()  # Strip to remove extra whitespace
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            return False

        # Parse Python code
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # Get problematic line for better error message
            lines = content.splitlines()
            if 0 <= e.lineno - 1 < len(lines):
                problematic_line = lines[e.lineno - 1]
                logger.error(f"Syntax error in file {filename}:")
                logger.error(f"Line {e.lineno}: {problematic_line}")
                logger.error(f"Error: {e.msg}")
                # Show position of error with caret
                logger.error(" " * (e.offset + 7) + "^")
            else:
                logger.error(f"Syntax error in file {filename} at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
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