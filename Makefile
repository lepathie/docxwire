# Setup environment
.PHONY: setup
setup:
	uv sync
	npm ci

# Run test suite with coverage
.PHONY: test
test:
	uv run pytest --cov=docxwire --cov-report=term-missing

# Run all checks
.PHONY: check
check:
	uv run ty check .
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

# Validate a commit message (piped via stdin)
.PHONY: lint-commit
lint-commit:
	./node_modules/.bin/commitlint $(ARGS)

# Validate OpenSpec artifacts
.PHONY: openspec-validate
openspec-validate:
	./node_modules/.bin/openspec validate --all
