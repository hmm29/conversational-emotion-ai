.PHONY: help install test lint format type-check clean run build docker-build docker-run docker-push

# Define variables
PYTHON = python3
PIP = pip3
PYTEST = pytest
BLACK = black
ISORT = isort
FLAKE8 = flake8
MYPY = mypy
STREAMLIT = streamlit
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Help message
define HELP_MESSAGE
Available commands:

  install      Install the package and development dependencies
  dev          Install the package in development mode
  test         Run tests
  test-cov     Run tests with coverage report
  lint         Check code style with flake8
  format       Format code with black and isort
  type-check   Run type checking with mypy
  clean        Remove build artifacts and cache
  run          Run the Streamlit application
  build        Build the Docker image
  up           Start the application with Docker Compose
  down         Stop the application and remove containers
  logs         View application logs
  help         Show this help message
endef
export HELP_MESSAGE

# Default target
help:
	@echo "$$HELP_MESSAGE"

# Installation
dev:
	$(PIP) install -e ".[dev]"
	pre-commit install

install:
	$(PIP) install -r requirements.txt

# Testing
test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Linting and formatting
lint:
	$(FLAKE8 src/ tests/

format:
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

type-check:
	$(MYPY) src/

# Cleaning
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '.coverage' -delete
	find . -type d -name 'htmlcov' -exec rm -rf {} +

# Running the application
run:
	$(STREAMLIT) run app.py

# Docker commands
build:
	$(DOCKER) build -t conversational-emotion-ai .

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

# Run all checks
check: lint type-check test

# Default target
.DEFAULT_GOAL := help
