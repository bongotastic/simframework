"""Event object stored in the scheduler queue.

An Event contains a `data` dictionary and a `timespan` (a `datetime.timedelta`)
that can be used by handlers when processing the event. `timespan` defaults to
zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid runtime import cycles; used only for type checking and hints.
    from .scope import Scope
    from .system import SystemInstance


@dataclass
class Event:
    data: Dict[str, Any] = field(default_factory=dict)
    timespan: datetime.timedelta = field(default_factory=lambda: datetime.timedelta(0))
    category: Optional[str] = None
    scope: Optional["Scope"] = None
    system: Optional["SystemInstance"] = None

    def __repr__(self) -> str:  # pragma: no cover - trivial
        parts = [f"data={self.data!r}", f"timespan={self.timespan}"]
        if self.category is not None:
            parts.append(f"category={self.category!r}")
        if self.scope is not None:
            parts.append(f"scope={self.scope!r}")
        if self.system is not None:
            parts.append(f"system={self.system!r}")
        return f"Event({', '.join(parts)})"
