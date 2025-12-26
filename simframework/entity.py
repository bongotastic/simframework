"""Basic entity abstraction for simulation participants."""
from typing import Any

class Entity:
    def __init__(self, name: str):
        self.name = name

    def on_event(self, *args, **kwargs) -> Any:
        """Handle an event. Override in subclasses."""
        return None
