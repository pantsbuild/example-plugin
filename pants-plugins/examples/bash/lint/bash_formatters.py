# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""Setup for formatters for Bash.

You need to have this file for each distinct "language", such as Python or Java. This allows Pants
to group all relevant formatters together, such as all Bash formatters together and all Python
formatters together. See https://www.pantsbuild.org/v2.0/docs/plugins-fmt-goal.
"""

from dataclasses import dataclass
from typing import Iterable, List, Type

from pants.core.goals.fmt import FmtResult, LanguageFmtResults, LanguageFmtTargets
from pants.core.goals.style_request import StyleRequest
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.fs import Digest, Snapshot
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.unions import UnionMembership, UnionRule, union

from examples.bash.target_types import BashSources


@dataclass(frozen=True)
class BashFmtTargets(LanguageFmtTargets):
    required_fields = (BashSources,)


@union
class BashFmtRequest(StyleRequest):
    pass


@rule
async def format_bash_targets(
    bash_fmt_targets: BashFmtTargets, union_membership: UnionMembership
) -> LanguageFmtResults:
    original_sources = await Get(
        SourceFiles,
        SourceFilesRequest(target[BashSources] for target in bash_fmt_targets.targets),
    )
    prior_formatter_result = original_sources.snapshot

    results: List[FmtResult] = []
    fmt_request_types: Iterable[Type[BashFmtRequest]] = union_membership.union_rules[
        BashFmtRequest
    ]
    for fmt_request_type in fmt_request_types:
        result = await Get(
            FmtResult,
            BashFmtRequest,
            fmt_request_type(
                (
                    fmt_request_type.field_set_type.create(target)
                    for target in bash_fmt_targets.targets
                ),
                prior_formatter_result=prior_formatter_result,
            ),
        )
        results.append(result)
        if result.did_change:
            prior_formatter_result = await Get(Snapshot, Digest, result.output)
    return LanguageFmtResults(
        tuple(results),
        input=original_sources.snapshot.digest,
        output=prior_formatter_result.digest,
    )


def rules():
    return [*collect_rules(), UnionRule(LanguageFmtTargets, BashFmtTargets)]
