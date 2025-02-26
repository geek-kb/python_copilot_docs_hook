from setuptools import setup, find_packages

setup(
    name='python_copilot_docs_hook',
    version='0.1.21',
    packages=find_packages(),
    install_requires=[
        'openai>=1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'python-copilot-docs=python_copilot_docs_hook.main:main',
        ],
    },
)
