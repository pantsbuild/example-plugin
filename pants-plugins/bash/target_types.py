# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# Refer to https://pants.readme.io/v2.0/docs/target-api-concepts.

from pants.engine.target import COMMON_TARGET_FIELDS, Dependencies, Sources, Target


class BashSources(Sources):
    default = ("*.sh",)


class BashTarget(Target):
    alias = "bash"
    core_fields = (*COMMON_TARGET_FIELDS, Dependencies, BashSources)
