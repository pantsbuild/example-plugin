# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-test-goal.

This plugin uses the Shunit2 test runner script (https://github.com/kward/shunit2). Because the
test runner is a simple Bash script, we simply download the file to be able to run it. Shunit2
requires that tests have "source ./shunit2" at the bottom of the tests; as a convenience, our
plugin uses file system operations to automatically add that line to any test files missing it.
After setting up the source files (including finding all relevant transitive dependencies), we run
the equivalent of `bash test_file.sh`.

We must implement rules for both normal `test` and `test --debug`. To deduplicate, we have a
common `TestSetup` type and rule to set up the test.
"""

from dataclasses import dataclass

from pants.core.goals.test import TestDebugRequest, TestFieldSet, TestResult
from pants.core.target_types import FilesSources, ResourcesSources
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Addresses
from pants.engine.fs import (
    CreateDigest,
    Digest,
    DigestContents,
    DownloadFile,
    FileContent,
    MergeDigests,
)
from pants.engine.process import FallibleProcessResult, InteractiveProcess, Process
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import Dependencies, Sources, TransitiveTargets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from examples.bash.bash_setup import BashProgram, BashSetup
from examples.bash.target_types import BashSources, BashTestSources


@dataclass(frozen=True)
class Shunit2FieldSet(TestFieldSet):
    required_fields = (BashTestSources,)

    sources: BashTestSources
    dependencies: Dependencies


@dataclass(frozen=True)
class TestSetupRequest:
    field_set: Shunit2FieldSet


@dataclass(frozen=True)
class TestSetup:
    process: Process


@rule(level=LogLevel.DEBUG)
async def setup_shunit2_for_target(
    request: TestSetupRequest, bash_program: BashProgram, bash_setup: BashSetup
) -> TestSetup:
    # Because shunit2 is a simple Bash file, we download it using `DownloadFile`. Normally, we
    # would install the test runner through `ExternalTool`. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools and
    # https://www.pantsbuild.org/v2.0/docs/rules-api-file-system.
    shunit2_script_request = Get(
        Digest,
        DownloadFile(
            url="https://raw.githubusercontent.com/kward/shunit2/b9102bb763cc603b3115ed30a5648bf950548097/shunit2",
            expected_digest=Digest(
                "1f11477b7948150d1ca50cdd41d89be4ed2acd137e26d2e0fe23966d0e272cc5",
                40987,
            ),
        ),
    )

    transitive_targets_request = Get(
        TransitiveTargets, Addresses([request.field_set.address])
    )

    shunit2_script, transitive_targets = await MultiGet(
        shunit2_script_request, transitive_targets_request
    )

    # We need to include all relevant transitive dependencies in the environment. We also get the
    # test's sources so that we can check that it has `source ./shunit2` at the bottom of it.
    #
    # Because we might modify the test files, we leave the tests out of
    # `dependencies_source_files_request` by using `transitive_targets.dependencies` instead of
    # `transitive_targets.closure`. This makes sure that we don't accidentally include the
    # unmodified test files and the modified test files in the same input. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-and-target-api.
    dependencies_source_files_request = Get(
        SourceFiles,
        SourceFilesRequest(
            (tgt.get(Sources) for tgt in transitive_targets.dependencies),
            for_sources_types=(BashSources, FilesSources, ResourcesSources),
        ),
    )
    test_source_files_request = Get(
        SourceFiles, SourceFilesRequest([request.field_set.sources])
    )
    dependencies_source_files, test_source_files = await MultiGet(
        dependencies_source_files_request, test_source_files_request
    )

    # To check if the test files already have `source ./shunit2` in them, we need to look at the
    # actual file content. We use `DigestContents` for this, and then use `CreateDigest` to create
    # a digest of the (possibly) updated test files. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-file-system.
    #
    # Most test runners don't modify their test files like we do here, so most test runners can
    # skip this step.
    test_files_content = await Get(
        DigestContents, Digest, test_source_files.snapshot.digest
    )
    updated_test_files_content = []
    for file_content in test_files_content:
        if (
            b"source ./shunit2" in file_content.content
            or b". ./shunit2" in file_content.content
        ):
            updated_test_files_content.append(file_content)
        else:
            updated_file_content = FileContent(
                path=file_content.path,
                content=file_content.content + b"\nsource ./shunit2\n",
            )
            updated_test_files_content.append(updated_file_content)
    updated_test_source_files = await Get(
        Digest, CreateDigest(updated_test_files_content)
    )

    # The Process needs one single `Digest`, so we merge everything together. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-file-system.
    input_digest = await Get(
        Digest,
        MergeDigests(
            [
                shunit2_script,
                updated_test_source_files,
                dependencies_source_files.snapshot.digest,
            ]
        ),
    )

    process = Process(
        argv=[bash_program.exe, *test_source_files.snapshot.files],
        input_digest=input_digest,
        description=f"Run shunit2 on {request.field_set.address}.",
        level=LogLevel.DEBUG,
        env=bash_setup.env_dict,
    )
    return TestSetup(process)


@rule(desc="Run tests with Shunit2", level=LogLevel.DEBUG)
async def run_tests_with_shunit2(field_set: Shunit2FieldSet) -> TestResult:
    setup = await Get(TestSetup, TestSetupRequest(field_set))
    # We use `FallibleProcessResult`, rather than `ProcessResult`, because we're okay with the
    # Process failing.
    result = await Get(FallibleProcessResult, Process, setup.process)
    return TestResult.from_fallible_process_result(result)


@rule(desc="Setup Shunit2 to run interactively", level=LogLevel.DEBUG)
async def setup_shunit2_debug_test(field_set: Shunit2FieldSet) -> TestDebugRequest:
    setup = await Get(TestSetup, TestSetupRequest(field_set))
    # We set up an InteractiveProcess, which will get run in the `@goal_rule` in `test.py`.
    return TestDebugRequest(
        InteractiveProcess(
            argv=setup.process.argv,
            # env=setup.process.env,
            input_digest=setup.process.input_digest,
        ),
    )


def rules():
    return (*collect_rules(), UnionRule(TestFieldSet, Shunit2FieldSet))
