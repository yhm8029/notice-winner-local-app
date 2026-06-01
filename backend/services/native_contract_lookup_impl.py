from __future__ import annotations

import sys as _sys

from . import native_contract_lookup_runtime as _runtime

_sys.modules[__name__] = _runtime
