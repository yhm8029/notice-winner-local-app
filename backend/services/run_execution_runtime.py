from __future__ import annotations

import sys as _sys

from . import run_execution_core_runtime as _core

_sys.modules[__name__] = _core
