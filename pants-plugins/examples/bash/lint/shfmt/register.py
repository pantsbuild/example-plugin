# Copyright 2020 Pants project contributors.
# Licensed under the Apache License, Version 2.0 (see LICENSE).

# Note that we use a separate `register.py` than the main `examples/bash/register.py` so that users
# must opt into activating Shellcheck. We could have instead registered the Shellcheck rules there
# if we were okay with Shellcheck being activated when the Shell backend is activated.

from examples.bash.lint import bash_formatters
from examples.bash.lint.shfmt.rules import rules as shfmt_rules


def rules():
    return [*shfmt_rules(), *bash_formatters.rules()]
