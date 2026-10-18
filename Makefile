# Setup environment
.PHONY: setup
setup:
	uv sync

# Run all checks
.PHONY: check
check:
	uv run pymarkdown scan -r --respect-gitignore .

# Auto-fix findings
.PHONY: fix
fix:
	uv run pymarkdown fix -r --respect-gitignore .
