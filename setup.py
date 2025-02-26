from setuptools import setup, find_packages

setup(
    name='python_copilot_docs_hook',
    version='0.1.16',
    packages=find_packages(),
    install_requires=[
        'openai>=1.0.0',
        'requests>=2.25.0',
    ],
    entry_points={
        'console_scripts': [
            'python-copilot-docs=python_copilot_docs_hook.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
