# Setup environment
.PHONY: setup
setup:
	uv sync
	npm ci

# Run test suite with coverage
.PHONY: test
test:
	uv run pytest --cov=docxwire --cov-report=term-missing

# Lint Python and markdown
.PHONY: lint
lint:
	uv run ty check .
	uv run ruff check .
	uv run ruff format --check .
	uv run pymarkdown scan -r --respect-gitignore .

# Validate OpenSpec artifacts and generated-file sync
.PHONY: check-specs
check-specs:
	./node_modules/.bin/openspec validate --all
	test "$$(./node_modules/.bin/openspec update --dry-run --json | jq '[.changes[] | select(.path | startswith("~") | not)] | length')" -eq 0

# Check the engines.node floor matches the dependency tree's minimum
.PHONY: check-deps
check-deps:
	node scripts/check-node-engines.mjs

# Run all checks
.PHONY: check
check: lint check-specs check-deps

# Full CI (all checks + tests)
.PHONY: ci
ci: check test

# Auto-fix findings
.PHONY: fix
fix:
	uv run ruff check --fix .
	uv run ruff format .
	uv run pymarkdown fix -r --respect-gitignore .
	node scripts/check-node-engines.mjs --fix
	./node_modules/.bin/openspec update

# Validate a commit message (piped via stdin)
.PHONY: lint-commit
lint-commit:
	./node_modules/.bin/commitlint $(ARGS)
