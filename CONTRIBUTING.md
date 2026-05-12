# Contributing to Floe

Thank you for considering contributing to Floe. This document outlines the
process for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Convention](#commit-convention)
- [Pull Request Workflow](#pull-request-workflow)
- [Reporting Issues](#reporting-issues)

---

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/floe.git
cd floe

# Install dependencies
uv sync

# Create environment configuration
cp .env.example .env

# Edit .env with your credentials
```

### Run the bot

```bash
uv run python -m floe.main
```

### Run tests

```bash
uv run pytest
```

---

## Coding Standards

- **Line length:** 100 characters
- **String quotes:** double quotes (enforced by Ruff)
- **Type hints:** required for all function parameters and return values
- **Logging:** use module-level logger, never `print()`
- **Formatting:** Ruff (auto-format on save)

### Before submitting

Run all checks in order:

```bash
uv run ruff format src/
uv run ruff check src/
uv run ty check src/
uv run pytest
```

---

## Commit Convention

Use conventional commit messages:

```
type(scope): description
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

Examples:

```
feat(sheets): add delete_last_transaction function
fix(bot): handle empty user list at startup
docs: update README with configuration table
```

---

## Pull Request Workflow

1. Open an issue to discuss the change you want to make.
2. Fork the repository.
3. Create a branch: `feat/<issue-number>-<slug>`
4. Make atomic commits with conventional commit messages.
5. Run all checks (format, lint, typecheck, test) before submitting.
6. Open a pull request against the `main` branch.

### PR template

Include the following in your PR description:

- Summary of the change
- List of files modified and what changed
- How you tested the changes
- Any notes for the reviewer

---

## Reporting Issues

- Use the issue templates when submitting bug reports or feature requests.
- For security issues, do not open a public issue. Contact the maintainer directly.
