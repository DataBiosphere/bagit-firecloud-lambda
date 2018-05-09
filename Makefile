# Makefile
THIS_FILE := $(lastword $(MAKEFILE_LIST))

include common.mk

SHELL := /bin/bash
RUNTEST := -m unittest -v -b
ALLMODULES := $(patsubst %.py, %.py, $(wildcard tests/test_*.py))

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d .venvbag || virtualenv --python=python3.6 .venvbag
	.venvbag/bin/pip install -Ur requirements.txt
	touch .venvbag/bin/activate

tests: venv
	@echo "running tests"
	.venvbag/bin/python ${RUNTEST} ${ALLMODULES}

awssetup: tests
	@echo "setting up awscli"
	.venvbag/bin/pip install awscli --upgrade

deploy-dev: awssetup
	@echo "deploying to dev"
	.venvbag/bin/chalice deploy --stage dev

deploy-staging: awssetup
	@echo "deploying to staging"
	.venvbag/bin/chalice deploy --stage staging
