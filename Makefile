#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = spotify-api-examples
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python

include .env

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt


## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	poetry run flake8 spotify_api_examples
	poetry run isort --check --diff --profile black spotify_api_examples
	poetry run black --check --config pyproject.toml spotify_api_examples

## Format source code with black
.PHONY: format
format:
	poetry run isort spotify_api_examples
	poetry run black --config pyproject.toml spotify_api_examples

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Run SurrealDB
start_db:
	mkdir -p storage/surrealdb/
	docker run -d --rm --pull always -p "127.0.0.1:8000:8000" --user $(shell id -u) \
        -v $(shell pwd)/storage/surrealdb:/mydata surrealdb/surrealdb:latest start \
        --user ${SURREALDB_USER} --pass ${SURREALDB_PASS} \
        --log trace file:/mydata/mydatabase.db

## run dvc repro
.PHONE: repro
repro:
	poetry run dvc repro
	git commit dvc.lock -m 'dvc repro' || true

## Make Dataset
.PHONY: data
data: requirements
	$(PYTHON_INTERPRETER) spotify_api_examples/dataset.py


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
