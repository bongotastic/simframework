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
    from .entity import Entity


@dataclass
class Event:
    data: Dict[str, Any] = field(default_factory=dict)
    timespan: datetime.timedelta = field(default_factory=lambda: datetime.timedelta(0))
    scope: Optional["Scope"] = None
    entity_anchor: Optional["Entity"] = None

    def __repr__(self) -> str:  # pragma: no cover - trivial
        parts = [f"data={self.data!r}", f"timespan={self.timespan}"]
        if self.scope is not None:
            parts.append(f"scope={self.scope!r}")
        if self.entity_anchor is not None:
            parts.append(f"system={self.entity_anchor!r}")
        return f"Event({', '.join(parts)})"

    def set_property(self, key: str, value: Any) -> None:
        """Set a property on this Event's `data` dictionary.

        Args:
            key: The property key to set (typically a string).
            value: The value to assign.
        """
        self.data[key] = value

    def get_property(self, key: Any, default: Any = None) -> Any:
        """Return the value associated with `key` in the event's `data`.

        If the key is not present, return `default` (defaults to None).
        """
        return self.data.get(key, default)
