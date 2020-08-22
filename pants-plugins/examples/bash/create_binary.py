# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-binary-goal.

This plugin will simply create a `.zip` file with all the relevant files included. The user must
then unzip the file and run the relevant file.

A more robust `binary` implementation will create a single file that is runnable, such as a
PEX file or JAR file.
"""

from dataclasses import dataclass

from pants.core.goals.binary import BinaryFieldSet, CreatedBinary
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Addresses
from pants.engine.process import BinaryPathRequest, BinaryPaths, Process, ProcessResult
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Dependencies, Sources, TransitiveTargets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from examples.bash.target_types import BashBinarySources, BashSources


@dataclass(frozen=True)
class BashBinaryFieldSet(BinaryFieldSet):
    required_fields = (BashBinarySources,)

    sources: BashBinarySources
    dependencies: Dependencies


@rule(level=LogLevel.DEBUG)
async def create_bash_binary(field_set: BashBinaryFieldSet) -> CreatedBinary:
    # We first locate the `zip` program using `BinaryPaths`. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools.
    zip_program_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(binary_name="zip", search_path=["/bin", "/usr/bin"]),
    )
    if not zip_program_paths.first_path:
        raise ValueError(
            "Could not find the `zip` program on `/bin` or `/usr/bin`, so cannot create a binary "
            f"for {field_set.address}."
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

    output_filename = f"{field_set.address.target_name}.zip"
    result = await Get(
        ProcessResult,
        Process(
            argv=(
                zip_program_paths.first_path,
                output_filename,
                *sources.snapshot.files,
            ),
            input_digest=sources.snapshot.digest,
            description=f"Zip {field_set.address} and its dependencies.",
            output_files=(output_filename,),
        ),
    )
    return CreatedBinary(result.output_digest, binary_name=output_filename)


def rules():
    return (*collect_rules(), UnionRule(BinaryFieldSet, BashBinaryFieldSet))
