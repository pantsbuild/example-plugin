# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-package-goal.

This plugin will simply create a `.zip` file with all the relevant files included. The user must
then unzip the file and run the relevant file.

This duplicates the `archive` target type and is only used for instructional purposes.
"""

import os
from dataclasses import dataclass

from pants.core.goals.package import BuiltPackage, PackageFieldSet
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Addresses
from pants.engine.process import (
    BinaryPathRequest,
    BinaryPaths,
    BinaryPathTest,
    Process,
    ProcessResult,
)
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Sources, TransitiveTargets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from examples.bash.bash_setup import BashSetup
from examples.bash.target_types import BashBinarySources, BashSources


@dataclass(frozen=True)
class BashBinaryFieldSet(PackageFieldSet):
    required_fields = (BashBinarySources,)

    sources: BashBinarySources


@rule(level=LogLevel.DEBUG)
async def create_bash_binary(
    field_set: BashBinaryFieldSet, bash_setup: BashSetup
) -> BuiltPackage:
    # We first locate the `zip` program using `BinaryPaths`. We use the option
    # `--bash-executable-search-paths` to determine which paths to search, such as `/bin` and
    # `/usr/bin`. See https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools.
    zip_program_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(
            binary_name="zip",
            search_path=bash_setup.executable_search_path,
            # This will run `zip --version` to ensure it's a valid binary and to allow
            # invalidating the cache if the version changes.
            test=BinaryPathTest(args=["-v"]),
        ),
    )
    if not zip_program_paths.first_path:
        raise EnvironmentError(
            f"Could not find the `zip` program on search paths "
            f"{list(bash_setup.executable_search_path)}, so cannot create a binary for "
            f"{field_set.address}. Please check that `zip` is installed and possibly modify the "
            "option `executable_search_paths` in the `[bash-setup]` options scope."
        )

    # We need to include all relevant transitive dependencies in the zip. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-and-target-api.
    transitive_targets = await Get(TransitiveTargets, Addresses([field_set.address]))
    sources = await Get(
        SourceFiles,
        SourceFilesRequest(
            (tgt.get(Sources) for tgt in transitive_targets.closure),
            for_sources_types=(BashSources, FilesSources, ResourcesSources),
        ),
    )

    output_filename = os.path.join(
        field_set.address.spec_path.replace(os.sep, "."),
        f"{field_set.address.target_name}.zip",
    )
    result = await Get(
        ProcessResult,
        Process(
            argv=(
                zip_program_paths.first_path.path,
                output_filename,
                *sources.snapshot.files,
            ),
            input_digest=sources.snapshot.digest,
            description=f"Zip {field_set.address} and its dependencies.",
            output_files=(output_filename,),
        ),
    )
    return BuiltPackage(result.output_digest, relpath=output_filename)


def rules():
    return (*collect_rules(), UnionRule(PackageFieldSet, BashBinaryFieldSet))
