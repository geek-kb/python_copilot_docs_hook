# Python Copilot Documentation Hook

A pre-commit hook that checks Python files for missing documentation and suggests using GitHub Copilot for documentation generation.

## Installation

```bash
pip install python_copilot_docs_hook
```

## Usage

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/yourusername/python_copilot_docs_hook
    rev: v0.1.0
    hooks:
      - id: python-copilot-docs
```

## Requirements

- Python 3.6+
- GitHub Copilot subscription
- VS Code with Copilot extension

## How it Works

1. Hook checks Python files for missing documentation
2. If missing docs are found:
   - Shows line numbers where docs are needed
   - Suggests using Alt+\ to trigger Copilot suggestions
3. Commit fails if any files are missing documentation

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/python_copilot_docs_hook.git
cd python_copilot_docs_hook

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e .
```
