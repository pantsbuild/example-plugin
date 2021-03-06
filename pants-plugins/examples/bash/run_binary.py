# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-run-goal.

This plugin finds `bash` on the user's machine, gets all relevant
dependencies for the binary target, then runs the equivalent of `bash
my_script.sh`.
"""

import os
from dataclasses import dataclass

from pants.core.goals.run import RunFieldSet, RunRequest
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import Sources, TransitiveTargets, TransitiveTargetsRequest
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from examples.bash.bash_setup import BashProgram, BashSetup
from examples.bash.target_types import BashBinarySources, BashSources


@dataclass(frozen=True)
class BashRunFieldSet(RunFieldSet):
    required_fields = (BashBinarySources,)

    sources: BashBinarySources


@rule(level=LogLevel.DEBUG)
async def run_bash_binary(
    field_set: BashRunFieldSet, bash_program: BashProgram, bash_setup: BashSetup
) -> RunRequest:
    transitive_targets = await Get(
        TransitiveTargets, TransitiveTargetsRequest([field_set.address])
    )

    # We need to include all relevant transitive dependencies in the environment. We also get the
    # binary's sources so that we know the script name. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-and-target-api.
    binary_sources_request = Get(SourceFiles, SourceFilesRequest([field_set.sources]))
    all_sources_request = Get(
        SourceFiles,
        SourceFilesRequest(
            (tgt.get(Sources) for tgt in transitive_targets.closure),
            for_sources_types=(BashSources, FilesSources, ResourcesSources),
        ),
    )
    binary_sources, all_sources = await MultiGet(
        binary_sources_request, all_sources_request
    )

    # We join the relative path to our program with the template string "{chroot}", which will get
    # substituted with the path to the temporary directory where our program runs. This ensures
    # that we run the correct file.
    # Note that `BashBinarySources` will have already validated that there is exactly one file in
    # the sources field.
    script_name = os.path.join("{chroot}", binary_sources.files[0])

    return RunRequest(
        digest=all_sources.snapshot.digest,
        args=[bash_program.exe, script_name],
        extra_env=bash_setup.env_dict,
    )


def rules():
    return (*collect_rules(), UnionRule(RunFieldSet, BashRunFieldSet))
