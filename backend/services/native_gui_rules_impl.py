from __future__ import annotations

from . import _native_gui_rules_impl as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)

__all__ = [name for name in dir(_impl) if not name.startswith("__")]

del _name
del _impl
