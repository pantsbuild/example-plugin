# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""Common setup for the Bash plugin, similar to Pants's `[python-setup]`
subsystem."""

import os
from dataclasses import dataclass
from typing import Tuple

from pants.engine.process import BinaryPathRequest, BinaryPaths
from pants.engine.rules import Get, collect_rules, rule
from pants.option.subsystem import Subsystem
from pants.util.frozendict import FrozenDict
from pants.util.logging import LogLevel
from pants.util.ordered_set import OrderedSet
from pants.util.strutil import create_path_env_var


# See https://www.pantsbuild.org/v2.0/docs/rules-api-subsystems.
class BashSetup(Subsystem):
    """Common setup for the Bash plugin."""

    options_scope = "bash-setup"

    @classmethod
    def register_options(cls, register):
        register(
            "--executable-search-paths",
            type=list,
            member_type=str,
            default=["<PATH>"],
            metavar="<binary-paths>",
            help=(
                "The PATH value that will be used by subprocesses spawned by the Bash plugin. The "
                "special string '<PATH>' will expand to the contents of the PATH env var."
            ),
        )

    @property
    def executable_search_path(self) -> Tuple[str, ...]:
        result = OrderedSet()
        for entry in self.options.executable_search_paths:
            if entry == "<PATH>":
                path = os.environ.get("PATH")
                if path:
                    for path_entry in path.split(os.pathsep):
                        result.add(path_entry)
            else:
                result.add(entry)
        return tuple(result)

    @property
    def env_dict(self) -> FrozenDict[str, str]:
        """Setup for the `env` for `Process`es that run Bash.

        Call sites must opt into using this value by requesting
        `BashSetup` as a parameter to their rule, then setting
        `env=bash_setup.env_dict` for any relevant `Process.`
        """
        return FrozenDict({"PATH": create_path_env_var(self.executable_search_path)})


@dataclass(frozen=True)
class BashProgram:
    exe: str


@rule(desc="Find Bash", level=LogLevel.DEBUG)
async def run_bash_binary(bash_setup: BashSetup) -> BashProgram:
    # We expect Bash to already be installed. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools.
    bash_program_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(binary_name="bash", search_path=bash_setup.executable_search_path),
    )
    if not bash_program_paths.first_path:
        raise EnvironmentError(
            "Could not find the `bash` program on `/bin` or `/usr/bin`, so this plugin cannot work."
        )
    return BashProgram(bash_program_paths.first_path)


def rules():
    return collect_rules()
