from setuptools import setup, find_packages

setup(
    name='python_copilot_docs_hook',
    version='0.1.12',
    description='A pre-commit hook to check Python documentation using GitHub Copilot',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Itai Ganot',
    author_email='lel@lel.bz',
    url='https://github.com/geek-kb/python_copilot_docs_hook',
    packages=find_packages(),
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
