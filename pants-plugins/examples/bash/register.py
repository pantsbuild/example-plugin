# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""The entry point for our `examples.bash` plugin.

See https://www.pantsbuild.org/v2.0/docs/plugins-overview.
"""

from examples.bash import (
    bash_setup,
    create_binary,
    repl,
    run_binary,
    shunit2_test_runner,
)
from examples.bash.target_types import BashBinary, BashLibrary, BashTests


def target_types():
    return [BashBinary, BashLibrary, BashTests]


def rules():
    return [
        *bash_setup.rules(),
        *create_binary.rules(),
        *repl.rules(),
        *run_binary.rules(),
        *shunit2_test_runner.rules(),
    ]
