# Setup environment
.PHONY: setup
setup:
	uv sync

# Run test suite with coverage
.PHONY: test
test:
	uv run pytest --cov=docxwire --cov-report=term-missing

# Run all checks
.PHONY: check
check:
	uv run ty check src/
	uv run ruff check .
	uv run ruff format --check .
	uv run pymarkdown scan -r --respect-gitignore .

# Full CI (lint + tests)
.PHONY: ci
ci: check test

# Auto-fix findings
.PHONY: fix
fix:
	uv run ruff check --fix .
	uv run ruff format .
	uv run pymarkdown fix -r --respect-gitignore .
