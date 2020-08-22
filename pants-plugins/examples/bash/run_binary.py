# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pants.core.goals.run import RunRequest
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Addresses
from pants.engine.process import BinaryPathRequest, BinaryPaths
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import Sources, TransitiveTargets
from pants.util.logging import LogLevel

from examples.bash.create_binary import BashBinaryFieldSet
from examples.bash.target_types import BashSources


@rule(level=LogLevel.DEBUG)
async def run_bash_binary(field_set: BashBinaryFieldSet) -> RunRequest:
    bash_program_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(binary_name="bash", search_path=["/bin", "/usr/bin"]),
    )
    if not bash_program_paths.first_path:
        raise ValueError(
            "Could not find the `bash` program on `/bin` or `/usr/bin`, so cannot run "
            f"{field_set.address}."
        )

    transitive_targets = await Get(TransitiveTargets, Addresses([field_set.address]))

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

    # Note that `BashBinarySources` will have already validated that there is exactly one file in
    # the sources field.
    script_name = binary_sources.files[0]

    return RunRequest(
        digest=all_sources.snapshot.digest,
        args=[bash_program_paths.first_path, script_name],
    )


def rules():
    return collect_rules()
