# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from examples.bash import create_binary, run_binary
from examples.bash.target_types import BashBinary, BashLibrary


def target_types():
    return [BashBinary, BashLibrary]


def rules():
    return [*create_binary.rules(), *run_binary.rules()]
