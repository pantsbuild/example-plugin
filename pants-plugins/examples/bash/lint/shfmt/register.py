# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""The entry point for our `examples.bash.lint.shfmt` plugin.

See https://www.pantsbuild.org/v2.0/docs/plugins-overview.

Note that we use a separate `register.py` than the main `examples/bash/register.py` so that users
must opt into activating shfmt. We could have instead registered the shfmt rules there
if we were okay with shfmt being activated when the Bash backend is activated.
"""

from examples.bash.lint import bash_formatters
from examples.bash.lint.shfmt.rules import rules as shfmt_rules


def rules():
    return [*shfmt_rules(), *bash_formatters.rules()]
