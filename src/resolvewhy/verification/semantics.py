"""Compatibility exports for the reusable production semantic evaluator.

The evaluator lives under ``resolvewhy.solving`` so semantic solving is not
coupled to the higher-level verification package.  This module remains as a
stable import path for existing callers in the Phase 4A implementation.
"""

from resolvewhy.solving.semantics import *  # noqa: F401,F403
