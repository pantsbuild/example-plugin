# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""Defines our target types for Bash.

See https://www.pantsbuild.org/v2.0/docs/target-api-concepts. This uses a common Pants pattern of
having distinct `library`, `binary`, and `tests` target types.
"""

from pants.core.goals.package import OutputPathField
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    Dependencies,
    IntField,
    Sources,
    Target,
)


class BashSources(Sources):
    # Normally, we would add `expected_file_extensions = ('.sh',)`, but Bash scripts don't need a
    # file extension, so we don't use this.
    pass


class BashLibrary(Target):
    alias = "bash_library"
    core_fields = (*COMMON_TARGET_FIELDS, Dependencies, BashSources)
    help = """Bash util code that is not directly run."""


class BashBinarySources(BashSources):
    required = True
    expected_num_files = 1


class BashBinary(Target):
    alias = "bash_binary"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        OutputPathField,
        Dependencies,
        BashBinarySources,
    )
    help = """A Bash file that may be directly run."""


class BashTestSources(BashSources):
    default = ("*_test.sh", "test_*.sh")


class BashTestTimeout(IntField):
    """Whether to time out after a certain amount of time.

    If unset, the test will never time out.
    """

    alias = "timeout"


class BashTests(Target):

    alias = "bash_tests"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        Dependencies,
        BashTestSources,
        BashTestTimeout,
    )
    help = """Bash tests that are run via `shunit2`.

    Refer to https://github.com/kward/shunit2. Pants will automatically
    add `source `./shunit2` to the bottom of your test file if it is not
    already there, and it will ensure that the script is available as a
    sibling to your test file.
    """
