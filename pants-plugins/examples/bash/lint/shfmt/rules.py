# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/plugins-fmt-goal.

This plugin installs shfmt, then runs it on the input files.

It provides rules for both `lint` and `fmt` so that shfmt is used with both goals. To deduplicate,
we have a common `Setup` type and a rule to set up shfmt.
"""

from dataclasses import dataclass

from pants.core.goals.fmt import FmtResult
from pants.core.goals.lint import LintRequest, LintResult, LintResults
from pants.core.util_rules.external_tool import (
    DownloadedExternalTool,
    ExternalToolRequest,
)
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.fs import Digest, GlobMatchErrorBehavior, MergeDigests, PathGlobs
from pants.engine.platform import Platform
from pants.engine.process import FallibleProcessResult, Process, ProcessResult
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import FieldSet
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel
from pants.util.strutil import pluralize

from examples.bash.lint.bash_formatters import BashFmtRequest
from examples.bash.lint.shfmt.subsystem import Shfmt
from examples.bash.target_types import BashSources


@dataclass(frozen=True)
class ShfmtFieldSet(FieldSet):
    required_fields = (BashSources,)

    sources: BashSources


class ShfmtRequest(BashFmtRequest, LintRequest):
    field_set_type = ShfmtFieldSet


@dataclass(frozen=True)
class SetupRequest:
    request: ShfmtRequest
    check_only: bool


@dataclass(frozen=True)
class Setup:
    process: Process
    original_digest: Digest


@rule(level=LogLevel.DEBUG)
async def setup_shfmt(setup_request: SetupRequest, shfmt: Shfmt) -> Setup:

    download_shfmt_request = Get(
        DownloadedExternalTool,
        ExternalToolRequest,
        shfmt.get_request(Platform.current),
    )

    # If the user specified `--shfmt-config`, we must search for the file they specified with
    # `PathGlobs` to include it in the `input_digest`. We error if the file cannot be found.
    # https://www.pantsbuild.org/v2.0/docs/rules-api-file-system.
    config_digest_request = Get(
        Digest,
        PathGlobs(
            globs=[shfmt.options.config] if shfmt.options.config else [],
            glob_match_error_behavior=GlobMatchErrorBehavior.error,
            description_of_origin="the option `--shfmt-config`",
        ),
    )

    source_files_request = Get(
        SourceFiles,
        SourceFilesRequest(
            field_set.sources for field_set in setup_request.request.field_sets
        ),
    )

    downloaded_shfmt, config_digest, source_files = await MultiGet(
        download_shfmt_request, config_digest_request, source_files_request
    )

    # If we were given an input digest from a previous formatter for the source files, then we
    # should use that input digest instead of the one we read from the filesystem.
    source_files_snapshot = (
        source_files.snapshot
        if setup_request.request.prior_formatter_result is None
        else setup_request.request.prior_formatter_result
    )

    # The Process needs one single `Digest`, so we merge everything together. See
    # https://www.pantsbuild.org/v2.0/docs/rules-api-file-system.
    input_digest = await Get(
        Digest,
        MergeDigests(
            (source_files_snapshot.digest, downloaded_shfmt.digest, config_digest)
        ),
    )

    argv = [
        downloaded_shfmt.exe,
        "-d" if setup_request.check_only else "-w",
        *shfmt.options.args,
        *source_files_snapshot.files,
    ]
    process = Process(
        argv=argv,
        input_digest=input_digest,
        output_files=source_files_snapshot.files,
        description=f"Run shfmt on {pluralize(len(setup_request.request.field_sets), 'file')}.",
        level=LogLevel.DEBUG,
    )
    return Setup(process, original_digest=source_files_snapshot.digest)


@rule(desc="Format with shfmt", level=LogLevel.DEBUG)
async def shfmt_fmt(request: ShfmtRequest, shfmt: Shfmt) -> FmtResult:
    if shfmt.options.skip:
        return FmtResult.noop()
    setup = await Get(Setup, SetupRequest(request, check_only=False))
    result = await Get(ProcessResult, Process, setup.process)
    return FmtResult.from_process_result(
        result, original_digest=setup.original_digest, formatter_name="shfmt"
    )


@rule(desc="Lint with shfmt", level=LogLevel.DEBUG)
async def shfmt_lint(request: ShfmtRequest, shfmt: Shfmt) -> LintResults:
    if shfmt.options.skip:
        return LintResults()
    setup = await Get(Setup, SetupRequest(request, check_only=True))
    # We use `FallibleProcessResult`, rather than `ProcessResult`, because we're okay with the
    # Process failing.
    result = await Get(FallibleProcessResult, Process, setup.process)
    return LintResults(
        [LintResult.from_fallible_process_result(result, linter_name="shfmt")]
    )


def rules():
    return [
        *collect_rules(),
        UnionRule(BashFmtRequest, ShfmtRequest),
        UnionRule(LintRequest, ShfmtRequest),
    ]
