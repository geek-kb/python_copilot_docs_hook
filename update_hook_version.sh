#!/bin/bash
set -e

# Check if version number is provided
if [ -z "$1" ]; then
    echo "Please provide version number (e.g., 0.1.6)"
    exit 1
fi

VERSION=$1
PACKAGE_DIR="python_copilot_docs_hook"

# Clean local environment
echo "Cleaning local environment..."
pip uninstall -y python_docs_hook 2>/dev/null || true
pip cache purge

# Get latest version from PyPI with error handling
echo "Checking PyPI versions..."
LATEST_VERSION=$(pip index versions python_docs_hook 2>/dev/null | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
if [ -z "$LATEST_VERSION" ]; then
    echo "Error: Could not fetch latest version from PyPI"
    exit 1
fi

echo "Current latest version on PyPI: $LATEST_VERSION"
echo "New version to publish: $VERSION"
read -p "Continue with version update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Update version in files
echo "Updating version in files..."
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" $PACKAGE_DIR/__init__.py
sed -i '' "s/version='.*'/version='$VERSION'/" setup.py

# Build package
echo "Building package..."
python3 -m build

# Upload to PyPI
echo "Uploading to PyPI..."
python3 -m twine upload dist/*

# Git operations
git add $PACKAGE_DIR/__init__.py setup.py
git commit -m "Bump version to $VERSION"
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin main
git push origin "v$VERSION"

echo "Successfully updated to version $VERSION"
