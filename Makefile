# LaView NVR Video Downloader Makefile
# This Makefile provides common development tasks for the project

# Variables
PYTHON_VERSION := 3.12
VENV_NAME := venv
PYTHON := ${VENV_NAME}/bin/python
PIP := ${VENV_NAME}/bin/pip
UV := ${VENV_NAME}/bin/uv
RUFF := ${VENV_NAME}/bin/ruff
PYTEST := ${VENV_NAME}/bin/pytest
BLACK := ${VENV_NAME}/bin/black
MYPY := ${VENV_NAME}/bin/mypy

# Project directories
SRC_DIR := laview_dl
TEST_DIR := tests
DIST_DIR := dist
BUILD_DIR := build

# Default target
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ${MAKEFILE_LIST} | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Virtual environment management
.PHONY: venv
venv: ${VENV_NAME} ## Create virtual environment

${VENV_NAME}: ## Create virtual environment if it doesn't exist
	python${PYTHON_VERSION} -m venv ${VENV_NAME}
	${PIP} install --upgrade pip setuptools wheel uv

# Development dependencies
.PHONY: dev-deps
dev-deps: ${VENV_NAME} ## Install development dependencies
	${UV} pip install --python ${PYTHON} ruff black mypy pytest pytest-cov pre-commit build

# Production dependencies
.PHONY: deps
deps: ${VENV_NAME} ## Install production dependencies
	${UV} pip install --python ${PYTHON} -r requirements.txt

# Install all dependencies
.PHONY: install
install: ${VENV_NAME} ## Install all dependencies
	${UV} pip install --python ${PYTHON} -r requirements.txt
	${UV} pip install --python ${PYTHON} ruff black mypy pytest pytest-cov pre-commit build

# Install package in development mode
.PHONY: install-dev
install-dev: install ## Install package in development mode
	${UV} pip install --python ${PYTHON} -e .

# Install package system-wide using pipx
.PHONY: pipx
pipx: ## Install package system-wide using pipx
	pipx install .

# Install package system-wide using pipx in editable mode
.PHONY: pipx-dev
pipx-dev: ## Install package system-wide using pipx in editable mode
	pipx install --editable .

# Uninstall package from pipx
.PHONY: pipx-uninstall
pipx-uninstall: ## Uninstall package from pipx
	pipx uninstall laview_dl

# Ensure pipx path is in PATH
.PHONY: pipx-ensurepath
pipx-ensurepath: ## Ensure pipx path is in PATH
	pipx ensurepath

# Code formatting with ruff
.PHONY: format
format: ${VENV_NAME} ## Format code using ruff
	${RUFF} format ${SRC_DIR} ${TEST_DIR}

# Code linting with ruff
.PHONY: lint
lint: ${VENV_NAME} ## Lint code using ruff
	${RUFF} check ${SRC_DIR} ${TEST_DIR}

# Type checking with mypy
.PHONY: type-check
type-check: ${VENV_NAME} ## Run type checking with mypy
	${MYPY} ${SRC_DIR}

# Run all code quality checks
.PHONY: check
check: lint type-check ## Run all code quality checks (lint + type-check)

# Run all code quality checks and formatting
.PHONY: quality
quality: format check ## Format code and run all quality checks

# Testing
.PHONY: test
test: ${VENV_NAME} ## Run tests
	${PYTEST} ${TEST_DIR} -v

.PHONY: test-cov
test-cov: ${VENV_NAME} ## Run tests with coverage
	${PYTEST} ${TEST_DIR} --cov=${SRC_DIR} --cov-report=html --cov-report=term-missing

.PHONY: test-cov-xml
test-cov-xml: ${VENV_NAME} ## Run tests with XML coverage report
	${PYTEST} ${TEST_DIR} --cov=${SRC_DIR} --cov-report=xml

# Pre-commit hooks
.PHONY: pre-commit-install
pre-commit-install: ${VENV_NAME} ## Install pre-commit hooks
	${PYTHON} -m pre_commit install

.PHONY: pre-commit-run
pre-commit-run: ${VENV_NAME} ## Run pre-commit hooks on all files
	${PYTHON} -m pre_commit run --all-files

# Package management
.PHONY: build
build: ${VENV_NAME} ## Build package
	${PIP} install build
	${PYTHON} -m build

.PHONY: clean
clean: ## Clean build artifacts
	rm -rf ${DIST_DIR} ${BUILD_DIR} *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: uninstall
uninstall: ${VENV_NAME} ## Uninstall package
	${PIP} uninstall -y laview_dl || true

.PHONY: clean-all
clean-all: clean uninstall ## Clean everything including virtual environment
	rm -rf ${VENV_NAME}

# Development workflow
.PHONY: dev-setup
dev-setup: install-dev pre-commit-install ## Complete development setup
	@echo "Development environment setup complete!"

.PHONY: dev-check
dev-check: quality test ## Run all development checks

# Documentation
.PHONY: docs
docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"

# Security checks
.PHONY: security
security: ${VENV_NAME} ## Run security checks
	${PIP} install safety
	${VENV_NAME}/bin/safety check

# Dependency management
.PHONY: update-deps
update-deps: ${VENV_NAME} ## Update all dependencies
	${PIP} install --upgrade -r requirements.txt
	${PIP} install --upgrade ruff black mypy pytest pytest-cov pre-commit

.PHONY: freeze-deps
freeze-deps: ${VENV_NAME} ## Freeze current dependencies
	${PIP} freeze > requirements-frozen.txt

# CI/CD helpers
.PHONY: ci
ci: check test ## Run CI checks (lint + type-check + test)

.PHONY: ci-full
ci-full: quality test-cov security ## Run full CI pipeline

# Quick development commands
.PHONY: quick-test
quick-test: ${VENV_NAME} ## Quick test run
	${PYTEST} ${TEST_DIR} -x

.PHONY: quick-lint
quick-lint: ${VENV_NAME} ## Quick lint check
	${RUFF} check ${SRC_DIR} --select=E,F

# Utility commands
.PHONY: shell
shell: ${VENV_NAME} ## Activate virtual environment shell
	@echo "Activating virtual environment..."
	@echo "Run 'deactivate' to exit"
	@exec ${SHELL}

.PHONY: run
run: ${VENV_NAME} ## Run the CLI tool (example)
	${PYTHON} -m ${SRC_DIR}.cli --help

# Default target
.DEFAULT_GOAL := help

