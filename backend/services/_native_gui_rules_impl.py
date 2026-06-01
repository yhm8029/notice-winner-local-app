from __future__ import annotations

from . import _native_gui_rules_core as _core

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

__all__ = [name for name in dir(_core) if not name.startswith("__")]

del _name
del _core
