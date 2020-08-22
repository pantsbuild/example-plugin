# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""Options for the Shellcheck linter.

We use `ExternalTool` so that we can easily install the pre-compiled binary. See
https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools and
https://www.pantsbuild.org/v2.0/docs/rules-api-subsystems.
"""

from pants.core.util_rules.external_tool import ExternalTool
from pants.engine.platform import Platform
from pants.option.custom_types import file_option, shell_str


class Shellcheck(ExternalTool):
    """A linter for shell scripts."""

    options_scope = "shellcheck"
    default_version = "v0.7.1"
    default_known_versions = [
        "v0.7.1|darwin|b080c3b659f7286e27004aa33759664d91e15ef2498ac709a452445d47e3ac23|1348272",
        "v0.7.1|linux|64f17152d96d7ec261ad3086ed42d18232fcb65148b44571b564d688269d36c8|1443836",
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
        return (
            f"https://github.com/koalaman/shellcheck/releases/download/{self.version}/"
            f"shellcheck-{self.version}.{plat_str}.x86_64.tar.xz"
        )

    def generate_exe(self, _: Platform) -> str:
        return f"./shellcheck-{self.version}/shellcheck"
