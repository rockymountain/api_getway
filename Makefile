# Makefile for DX VAS API Gateway
# Requires: Python >= 3.10, pip-tools

PYTHON = python3
PIP_COMPILE = pip-compile

REQ_IN = requirements.in
REQ_DEV_IN = requirements-dev.in
REQ_TXT = requirements.txt
REQ_DEV_TXT = requirements-dev.txt
TEMP_REQ_TXT = .tmp.requirements.txt
TEMP_REQ_DEV_TXT = .tmp.requirements-dev.txt

.PHONY: help install install-dev test test-cov lint format type-check check-req compile-req clean

help:
	@echo "📘 Available commands:"
	@echo "  make install         - Install runtime dependencies"
	@echo "  make install-dev     - Install dev + runtime deps"
	@echo "  make test            - Run all tests"
	@echo "  make test-cov        - Run tests with coverage"
	@echo "  make lint            - Run black, flake8, isort, mypy"
	@echo "  make type-check      - Run mypy static type checker"
	@echo "  make format          - Auto-format with black + isort"
	@echo "  make check-req       - Check if requirements files are up to date"
	@echo "  make compile-req     - Regenerate requirements.txt and dev.txt"
	@echo "  make clean           - Remove cache and __pycache__"

install:
	@echo "📦 Installing runtime dependencies..."
	@$(PYTHON) -m pip install -r $(REQ_TXT)

install-dev:
	@echo "📦 Installing dev dependencies..."
	@$(PYTHON) -m pip install -r $(REQ_DEV_TXT)

test:
	@echo "🔬 Running tests..."
	@pytest -q tests/

test-cov:
	@echo "📊 Running tests with coverage..."
	@pytest --cov=app --cov-report=term-missing tests/

lint:
	@echo "🔎 Running linters and format checks..."
	@flake8 app/ tests/
	@isort --check-only app/ tests/
	@black --check app/ tests/
	@$(MAKE) type-check

type-check:
	@echo "🔍 Running mypy static type checking..."
	@$(PYTHON) -m mypy app/ --ignore-missing-imports
	@echo "✅ Mypy static type checking complete."

format:
	@echo "🎨 Auto-formatting code..."
	@isort app/ tests/
	@black app/ tests/

check-req:
	@echo "🔍 Checking if requirements files are up to date..."
	@$(PIP_COMPILE) --quiet --output-file=$(TEMP_REQ_TXT) $(REQ_IN)
	@$(PIP_COMPILE) --quiet --output-file=$(TEMP_REQ_DEV_TXT) $(REQ_DEV_IN)
	@diff -q $(REQ_TXT) $(TEMP_REQ_TXT) || (echo "❗ $(REQ_TXT) is out of date. Run 'make compile-req'" && rm -f $(TEMP_REQ_TXT) $(TEMP_REQ_DEV_TXT) && exit 1)
	@diff -q $(REQ_DEV_TXT) $(TEMP_REQ_DEV_TXT) || (echo "❗ $(REQ_DEV_TXT) is out of date. Run 'make compile-req'" && rm -f $(TEMP_REQ_TXT) $(TEMP_REQ_DEV_TXT) && exit 1)
	@echo "✅ Requirements files are up to date."
	@rm -f $(TEMP_REQ_TXT) $(TEMP_REQ_DEV_TXT)

compile-req:
	@echo "📦 Compiling and upgrading $(REQ_IN) -> $(REQ_TXT)..."
	@$(PIP_COMPILE) --upgrade --output-file=$(REQ_TXT) $(REQ_IN)
	@echo "📦 Compiling and upgrading $(REQ_DEV_IN) -> $(REQ_DEV_TXT)..."
	@$(PIP_COMPILE) --upgrade --output-file=$(REQ_DEV_TXT) $(REQ_DEV_IN)
	@echo "✅ Requirements compilation and upgrade complete."

clean:
	@echo "🧹 Cleaning temporary files and caches..."
	@find . -type d -name '__pycache__' -exec rm -r {} +
	@rm -rf .pytest_cache .mypy_cache htmlcov dist build
