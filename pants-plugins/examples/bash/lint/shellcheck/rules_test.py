# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""See https://www.pantsbuild.org/v2.0/docs/rules-api-testing.

We use `RuleRunner` as a tightly controlled integration test.
"""

from typing import List, Optional, Sequence

import pytest
from pants.core.goals.lint import LintResult, LintResults
from pants.engine.addresses import Address
from pants.engine.fs import FileContent
from pants.engine.rules import QueryRule
from pants.engine.target import Target
from pants.option.options_bootstrapper import OptionsBootstrapper
from pants.testutil.option_util import create_options_bootstrapper
from pants.testutil.rule_runner import RuleRunner

from examples.bash.lint.shellcheck.rules import ShellcheckFieldSet, ShellcheckRequest
from examples.bash.lint.shellcheck.rules import rules as shellcheck_rules
from examples.bash.target_types import BashLibrary


@pytest.fixture
def rule_runner() -> RuleRunner:
    return RuleRunner(
        rules=[
            *shellcheck_rules(),
            QueryRule(LintResults, (ShellcheckRequest, OptionsBootstrapper)),
        ]
    )


GOOD_SOURCE = FileContent("good.sh", b"echo 'hello world'\n")
BAD_SOURCE = FileContent("bad.sh", b'if [ "$VAR" = ""]; then\n')


def make_target(
    rule_runner: RuleRunner,
    source_files: List[FileContent],
) -> Target:
    for source_file in source_files:
        rule_runner.create_file(source_file.path, source_file.content.decode())
    return BashLibrary(
        {},
        address=Address("", target_name="target"),
    )


def run_shellcheck(
    rule_runner: RuleRunner,
    targets: List[Target],
    *,
    config: Optional[str] = None,
    passthrough_args: Optional[str] = None,
    skip: bool = False,
) -> Sequence[LintResult]:
    args = ["--backend-packages=examples.bash"]
    if config:
        rule_runner.create_file(relpath=".bandit", contents=config)
        args.append("--shellcheck-config=.bandit")
    if passthrough_args:
        args.append(f"--shellcheck-args={passthrough_args}")
    if skip:
        args.append("--shellcheck-skip")
    results = rule_runner.request_product(
        LintResults,
        [
            ShellcheckRequest(ShellcheckFieldSet.create(tgt) for tgt in targets),
            create_options_bootstrapper(args=args),
        ],
    )
    return results.results


def test_skip(rule_runner: RuleRunner) -> None:
    target = make_target(rule_runner, [BAD_SOURCE])
    result = run_shellcheck(rule_runner, [target], skip=True)
    assert not result
