# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# Refer to https://www.pantsbuild.org/v2.0/docs/rules-api-installing-tools.

from pants.core.util_rules.external_tool import ExternalTool
from pants.engine.platform import Platform
from pants.option.custom_types import file_option, shell_str


class Shfmt(ExternalTool):
    """An autoformatter for shell scripts (https://github.com/mvdan/sh)."""

    options_scope = "shfmt"
    default_version = "v3.1.2"
    default_known_versions = [
        "v3.1.2|darwin|284674897e4f708a8b2e4b549af60ac01da648b9581dc7510c586ce41096edaa|3277184",
        "v3.1.2|linux|c5794c1ac081f0028d60317454fe388068ab5af7740a83e393515170a7157dce|3043328",
    ]

    @classmethod
    def register_options(cls, register):
        super().register_options(register)
        register(
            "--skip",
            type=bool,
            default=False,
            help="Don't use shfmt when running `./pants fmt` or `./pants lint`.",
        )
        register(
            "--args",
            type=list,
            member_type=shell_str,
            help=("Arguments to pass directly to shfmt, e.g. `--shfmt-args='-i 2'`.'"),
        )
        register(
            "--config",
            type=list,
            member_type=file_option,
            advanced=True,
            help="Path to `.editorconfig` file. This must be relative to the build root.",
        )

    def generate_url(self, plat: Platform) -> str:
        plat_str = "linux" if plat == Platform.linux else "darwin"
        return (
            f"https://github.com/mvdan/sh/releases/download/{self.version}/"
            f"shfmt_{self.version}_{plat_str}_amd64"
        )

    def generate_exe(self, plat: Platform) -> str:
        plat_str = "linux" if plat == Platform.linux else "darwin"
        return f"./shfmt_{self.version}_{plat_str}_amd64"
