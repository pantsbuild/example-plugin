# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from examples.bash import shellcheck
from examples.bash.target_types import BashTarget


def rules():
    return [*shellcheck.rules()]


def target_types():
    return [BashTarget]
