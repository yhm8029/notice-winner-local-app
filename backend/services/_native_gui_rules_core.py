from __future__ import annotations

from . import _native_gui_rules_runtime_support as _support

for _name in dir(_support):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_support, _name)

__all__ = [name for name in dir(_support) if not name.startswith("__")]

del _name
del _support
