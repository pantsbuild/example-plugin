# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from dataclasses import dataclass

from examples.bash.target_types import BashSources
from pants.core.goals.lint import LintRequest, LintResult, LintResults
from pants.core.util_rules.determine_source_files import (
    AllSourceFilesRequest,
    SourceFiles,
)
from pants.core.util_rules.external_tool import (
    DownloadedExternalTool,
    ExternalTool,
    ExternalToolRequest,
)
from pants.engine.fs import (
    Digest,
    GlobMatchErrorBehavior,
    MergeDigests,
    PathGlobs,
    Snapshot,
)
from pants.engine.platform import Platform
from pants.engine.process import FallibleProcessResult, Process
from pants.engine.rules import SubsystemRule, rule
from pants.engine.selectors import Get, MultiGet
from pants.engine.target import FieldSetWithOrigin
from pants.engine.unions import UnionRule
from pants.option.custom_types import file_option, shell_str
from pants.util.strutil import pluralize


class Shellcheck(ExternalTool):
    """A linter for shell scripts."""

    options_scope = "shellcheck"
    default_version = "0.7.1"
    default_known_versions = [
        "0.7.1|darwin|b080c3b659f7286e27004aa33759664d91e15ef2498ac709a452445d47e3ac23|1348272",
        "0.7.1|linux|64f17152d96d7ec261ad3086ed42d18232fcb65148b44571b564d688269d36c8|1443836",
    ]

    @classmethod
    def register_options(cls, register):
        super().register_options(register)
        register(
            "--skip",
            type=bool,
            default=False,
            help="Don't use Shellcheck when running `./pants lint`.",
        )
        register(
            "--args",
            type=list,
            member_type=shell_str,
            help=(
                "Arguments to pass directly to Shellcheck, e.g. `--shellcheck-args='-e SC20529'`.'"
            ),
        )
        register(
            "--config",
            type=list,
            member_type=file_option,
            advanced=True,
            help="Path to `.shellcheckrc`. This must be relative to the build root.",
        )

    def generate_url(self, plat: Platform) -> str:
        plat_str = "linux" if plat == Platform.linux else "darwin"
        "https://github.com/koalaman/shellcheck/releases/download/v0.7.1/shellcheck-v0.7.1.darwin.x86_64.tar.xz"
        return (
            f"https://github.com/koalaman/shellcheck/releases/download/v{self.options.version}/"
            f"shellcheck-v{self.options.version}.{plat_str}.x86_64.tar.xz"
        )

    def generate_exe(self, plat: Platform) -> str:
        return f"shellcheck-v{self.options.version}/shellcheck"


@dataclass(frozen=True)
class ShellcheckFieldSet(FieldSetWithOrigin):
    required_fields = (BashSources,)

    sources: BashSources


class ShellcheckRequest(LintRequest):
    field_set_type = ShellcheckFieldSet


@rule
async def run_shellcheck(
    request: ShellcheckRequest, shellcheck: Shellcheck
) -> LintResults:
    if shellcheck.options.skip:
        return LintResults()

    download_shellcheck_request = Get(
        DownloadedExternalTool,
        ExternalToolRequest,
        shellcheck.get_request(Platform.current),
    )

    sources_request = Get(
        SourceFiles,
        AllSourceFilesRequest(field_set.sources for field_set in request.field_sets),
    )

    # If the user specified `--shellcheck-config`, we must search for the file they specified with
    # `PathGlobs` to include it in the `input_digest`. We error if the file cannot be found.
    config_snapshot_request = Get(
        Snapshot,
        PathGlobs(
            globs=[shellcheck.options.config] if shellcheck.options.config else [],
            glob_match_error_behavior=GlobMatchErrorBehavior.error,
            description_of_origin="the option `--shellcheck-config`",
        ),
    )

    downloaded_shellcheck, sources, config_snapshot = await MultiGet(
        download_shellcheck_request, sources_request, config_snapshot_request
    )

    # The Process needs one single `Digest`, so we merge everything together.
    input_digest = await Get(
        Digest,
        MergeDigests(
            (
                downloaded_shellcheck.digest,
                sources.snapshot.digest,
                config_snapshot.digest,
            )
        ),
    )

    process_result = await Get(
        FallibleProcessResult,
        Process(
            argv=[
                downloaded_shellcheck.exe,
                *shellcheck.options.args,
                *sources.snapshot.files,
            ],
            input_digest=input_digest,
            description=f"Run Shellcheck on {pluralize(len(request.field_sets), 'target')}.",
        ),
    )
    result = LintResult.from_fallible_process_result(
        process_result, linter_name="Shellcheck"
    )
    return LintResults([result])


def rules():
    return [
        run_shellcheck,
        SubsystemRule(Shellcheck),
        UnionRule(LintRequest, ShellcheckRequest),
    ]
