# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-repl-goal.

This plugin sets up a very minimal REPL that populates the chroot with
the input targets and their dependencies, and then runs the equivalent
of `bash`.

TODO(#13): When used with Pantsd, this implementation results in a warning `Inappropriate ioctl
for device` due to the TTY not being set up properly.
"""

from dataclasses import dataclass

from pants.core.goals.repl import ReplImplementation, ReplRequest
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Sources
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from examples.bash.bash_setup import BashProgram, BashSetup
from examples.bash.target_types import BashSources


# Unlike the other plugin types (e.g `lint` and `test`), we do not set up a FieldSet. `repl.py`
# will give us the transitive closure of all input targets, rather than filtering out the targets.
@dataclass(frozen=True)
class BashRepl(ReplImplementation):
    name = "bash"


@rule(level=LogLevel.DEBUG)
async def create_bash_repl_request(
    repl: BashRepl, bash_setup: BashSetup, bash_program: BashProgram
) -> ReplRequest:
    # Normally, we would need to install a Repl program, such as Ammonite for Scala. For Bash, we
    # simply run the program found by our rule that returns `BashProgram`, which uses
    # `BinaryPaths`. See https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools.

    # `repl.targets` already includes the transitive closure of the input targets. We filter out
    # irrelevant soures.
    sources = await Get(
        SourceFiles,
        SourceFilesRequest(
            (tgt.get(Sources) for tgt in repl.targets),
            for_sources_types=(BashSources, FilesSources, ResourcesSources),
        ),
    )
    return ReplRequest(
        digest=sources.snapshot.digest,
        args=(bash_program.exe,),
        env=bash_setup.env_dict,
    )


def rules():
    return (*collect_rules(), UnionRule(ReplImplementation, BashRepl))
