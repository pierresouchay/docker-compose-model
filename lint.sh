#!/bin/sh
set -eu
isort src
ruff format
mypy src --install-types --non-interactive
flake8 --max-line-length 160 src
pylint src
