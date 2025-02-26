#!/usr/bin/env python3
"""Python documentation generator using OpenAI API."""

import logging
import os
import ast
import argparse
import openai
from openai import OpenAI
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('python_copilot_docs_hook')

def get_suggestion_openai(code: str, api_key: str) -> str:
    """Get documentation suggestion using OpenAI API.
    
    Args:
        code: Python code to document
        api_key: OpenAI API key
        
    Returns:
        str: Generated docstring or empty string on failure
    """
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a Python documentation expert. Generate clear, concise Google-style docstrings."
                },
                {
                    "role": "user", 
                    "content": (
                        "Write a docstring for this Python code. Include args, returns, and raises sections "
                        f"if applicable:\n\n{code}"
                    )
                }
            ],
            temperature=0.3,
            max_tokens=250
        )
        
        return format_suggestion(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"OpenAI API failed: {e}")
        return ""

def format_suggestion(text: str) -> str:
    """Format OpenAI output as a proper docstring.
    
    Args:
        text: Raw docstring from OpenAI
        
    Returns:
        str: Formatted docstring in Google style
    """
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
    """Validate Python file before processing.
    
    Args:
        filename: Path to the file to validate
        
    Returns:
        bool: True if file is valid Python file, False otherwise
    """
    if not os.path.isfile(filename):
        logger.error(f"File not found: {filename}")
        return False
        
    if not filename.endswith('.py'):
        logger.error(f"Not a Python file: {filename}")
        return False
        
    return True

def update_file_with_docs(filename: str, api_key: str) -> bool:
    """Update Python file with generated documentation.
    
    Args:
        filename: Path to the Python file
        api_key: OpenAI API key
        
    Returns:
        bool: True if file was updated successfully, False otherwise
    """
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
            module_doc = get_suggestion_openai(content, api_key)
            if module_doc:
                content = f'"""{module_doc}"""\n\n{content}'
                modified = True

        # Find and generate function docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                logger.debug(f"Generating docstring for function: {node.name}")
                func_code = ast.get_source_segment(content, node)
                doc = get_suggestion_openai(func_code, api_key)
                
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
        description='Add missing documentation to Python files using OpenAI'
    )
    parser.add_argument('filenames', nargs='*', help='Python files to process')
    parser.add_argument('--openai-key', help='OpenAI API key', required=True)
    args = parser.parse_args()

    try:
        # Process files
        exit_code = 0
        for filename in args.filenames:
            logger.debug(f"Processing file: {filename}")
            if not update_file_with_docs(filename, args.openai_key):
                exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Error processing files: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())