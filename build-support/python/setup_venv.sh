#!/usr/bin/env bash
# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# A simple script to set up a virtual environment (venv) with all the Python dependencies used in
# the project. This venv is useful for integrating with IDEs. See
# https://pants.readme.io/docs/python-third-party-dependencies.

PYTHON_BIN=python3.8
VIRTUALENV=build-support/python/.venv
PIP="${VIRTUALENV}/bin/pip"

"${PYTHON_BIN}" -m venv "${VIRTUALENV}"
"${PIP}" install pip --upgrade
"${PIP}" install -r <(
  ./pants --no-pantsd dependencies --type=3rdparty --transitive ::
)
