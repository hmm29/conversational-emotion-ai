# Contributing to Conversational Emotion AI

Thank you for your interest in contributing to Conversational Emotion AI! We welcome contributions from the community to help improve this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please [open an issue](https://github.com/yourusername/conversational-emotion-ai/issues) with the following information:

- A clear and descriptive title
- A detailed description of the issue or feature request
- Steps to reproduce the issue (if applicable)
- Expected vs. actual behavior
- Screenshots or error messages (if applicable)
- Your environment (OS, Python version, etc.)

### Making Changes

1. **Fork the repository** and create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Set up the development environment**:
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   pre-commit install
   ```

3. **Make your changes** and ensure tests pass:
   ```bash
   # Run tests
   pytest
   
   # Run type checking
   mypy src/
   
   # Run linters
   black --check .
   isort --check-only .
   flake8
   ```

4. **Commit your changes** with a descriptive commit message:
   ```bash
   git commit -m "Add feature: brief description of changes"
   ```

5. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a pull request** with a clear title and description of your changes.

## Development Guidelines

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes following [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep lines under 88 characters (Black's default)

### Testing

- Write tests for all new functionality
- Aim for good test coverage (at least 80%)
- Tests should be fast, isolated, and deterministic
- Use descriptive test function names (e.g., `test_function_name_expected_behavior`)

### Documentation

- Update the README.md with any changes to setup, configuration, or usage
- Add docstrings for all public functions and classes
- Include examples in docstrings where helpful

## Review Process

1. A maintainer will review your pull request and provide feedback
2. Address any feedback and update your pull request
3. Once approved, a maintainer will merge your changes

## Getting Help

If you have questions or need help, please open an issue or reach out to the maintainers.

Thank you for contributing to Conversational Emotion AI!
