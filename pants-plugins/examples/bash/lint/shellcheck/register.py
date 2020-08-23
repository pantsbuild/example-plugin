# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""The entry point for our `examples.bash.lint.shellcheck` plugin.

See https://www.pantsbuild.org/v2.0/docs/plugins-overview.

Note that we use a separate `register.py` than the main `examples/bash/register.py` so that users
must opt into activating Shellcheck. We could have instead registered the Shellcheck rules there
if we were okay with Shellcheck always being activated when the Bash backend is activated.
"""

from examples.bash.lint.shellcheck.rules import rules as shellcheck_rules


def rules():
    return shellcheck_rules()
