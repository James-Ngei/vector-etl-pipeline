# Contributing to Vector ETL Pipeline

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository:**
```bash
   git clone https://github.com/James-Ngei/vector-etl-pipeline
   cd vector-etl-pipeline
```

2. **Install Poetry:**
```bash
   curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies:**
```bash
   poetry install
```

4. **Run tests:**
```bash
   poetry run pytest tests/ --cov=src
```

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow these guidelines:
- Write tests first (TDD approach)
- Maintain 95%+ test coverage
- Follow existing code style
- Add docstrings to public functions

### 3. Run Quality Checks
```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/ --ignore-missing-imports

# Run tests
poetry run pytest tests/ --cov=src
```

### 4. Commit

Follow conventional commits:
```bash
git commit -m "feat: add new validation rule"
git commit -m "fix: handle edge case in geometry repair"
git commit -m "docs: update API reference"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

- **Formatting:** Black (line length 88)
- **Linting:** Ruff
- **Type hints:** Use throughout
- **Docstrings:** Google style

## Testing Guidelines

- **Unit tests:** Mock external dependencies
- **Integration tests:** Only in CI/CD
- **Performance tests:** Use pytest-benchmark
- **Coverage:** Maintain 95%+ coverage

## Project Structure
```
src/
├── pipeline/      # Core ETL modules
├── config/        # Configuration
└── cli.py         # Command-line interface

tests/
├── unit/          # Fast, mocked tests
├── integration/   # Database tests (CI only)
└── performance/   # Benchmark tests
```

## Questions?

Open an issue or start a discussion!

## License

MIT License - see LICENSE file for details.
```

---

## Step 3: Add a LICENSE file

Create `LICENSE`:
```
MIT License

Copyright (c) 2026 James Ngei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.