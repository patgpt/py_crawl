# 🤝 Contributing to py_crawl

First off, thanks for taking the time to contribute! 🎉

## 📋 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## 🚀 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain the behavior you expected to see
* Explain why this enhancement would be useful

### 🔧 Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints

## 💻 Development Process

1. **Set up your environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Format your code**
   ```bash
   black .
   ```

## 📝 Style Guidelines

### 💭 Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### 🐍 Python Style Guide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://github.com/psf/black) for code formatting
* Add type hints to function definitions
* Write docstrings for all public methods and functions

### 📚 Documentation Style Guide

* Use Markdown for documentation
* Include code examples when relevant
* Keep line length to 80 characters
* Add docstrings to all public methods and classes

## 🏷️ Issue and Pull Request Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention is needed |

## ⚙️ Project Structure

```
py_crawl/
├── app/
│   ├── routes/
│   ├── schemas/
│   └── main.py
├── tests/
├── docs/
└── requirements.txt
```

## 📫 Contact

* Open an issue
* Start a discussion
* Join our community chat

Thank you for contributing to py_crawl! 🎉