#!/usr/bin/env bash
# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# This script is useful to set up a virtual environment so that IDEs understand the Python code.
# See https://www.pantsbuild.org/docs/python-third-party-dependencies.

PYTHON_BIN=python3.6
VIRTUALENV=build-support/python/.venv
PIP="${VIRTUALENV}/bin/pip"

"${PYTHON_BIN}" -m venv "${VIRTUALENV}"
"${PIP}" install pip --upgrade
"${PIP}" install -r <(./pants dependencies --type=3rdparty ::)
