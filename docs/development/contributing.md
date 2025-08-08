# Contributing to MCP Studio

Thank you for considering contributing to MCP Studio! We welcome all contributions, from bug reports to new features and documentation improvements.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
   ```bash
   git clone https://github.com/your-username/mcp-studio.git
   cd mcp-studio
   ```
3. Set up the development environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]
   pre-commit install
   ```
4. Create a branch for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. Make your changes
2. Run tests and linters
   ```bash
   pre-commit run --all-files
   pytest
   ```
3. Commit your changes with a descriptive message
   ```bash
   git commit -m "feat: add amazing feature"
   ```
4. Push to your fork and create a pull request

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **Mypy** for static type checking

These are automatically checked by pre-commit hooks.

## Testing

All code changes should include appropriate tests. To run the test suite:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

## Pull Request Process

1. Ensure your code passes all tests and linting checks
2. Update the documentation if necessary
3. Add your changes to the `CHANGELOG.md` file
4. Open a pull request with a clear description of your changes
5. Ensure all CI checks pass
6. Request a review from a maintainer

## Reporting Bugs

Please open an issue with:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Environment details (OS, Python version, etc.)
5. Any relevant logs or screenshots

## Feature Requests

We welcome feature requests! Please open an issue with:

1. A clear, descriptive title
2. A detailed description of the feature
3. The problem it solves
4. Any potential implementation ideas

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
