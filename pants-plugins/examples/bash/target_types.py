# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# Refer to https://www.pantsbuild.org/v2.0/docs/target-api-concepts.

from pants.engine.target import COMMON_TARGET_FIELDS, Dependencies, Sources, Target


class BashSources(Sources):
    # Normally, we would add `expected_file_extensions = ('.sh',)`, but Bash scripts don't need a
    # file extension, so we don't use this.
    pass


class BashLibrary(Target):
    """Bash util code that is not directly run."""

    alias = "bash_library"
    core_fields = (*COMMON_TARGET_FIELDS, Dependencies, BashSources)


class BashBinarySources(BashSources):
    expected_num_files = 1


class BashBinary(Target):
    """A Bash file that may be directly run."""

    alias = "bash_binary"
    core_fields = (*COMMON_TARGET_FIELDS, Dependencies, BashBinarySources)
