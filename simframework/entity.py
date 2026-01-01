"""Basic entity abstraction for simulation participants."""
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Entity:
    """An entity representing a physical object in the simulation.

    Entities model tools, containers, inputs, outputs, and other tangible objects.
    Each entity has:
    - identifier: A taxonomy-based identifier (e.g., Scope path or unique name)
    - reliability: A measure of functionality (0-10 scale)
    - ablative: A measure of wear/degradation (0-1 scale, where 1 = fully degraded)
    """

    identifier: str  # From domain taxonomy (e.g., "environment/temperature/sensor")
    reliability: float = 10.0  # 0-10 scale (10 = fully reliable, 0 = non-functional)
    ablative: float = 0.0  # 0-1 scale (0 = no degradation, 1 = completely ablated)
    location: Optional[Any] = None  # Optional system instance representing entity location

    def __post_init__(self) -> None:
        """Validate reliability and ablative values are within bounds."""
        if not 0.0 <= self.reliability <= 10.0:
            raise ValueError(f"reliability must be between 0 and 10; got {self.reliability}")
        if not 0.0 <= self.ablative <= 1.0:
            raise ValueError(f"ablative must be between 0 and 1; got {self.ablative}")

    @property
    def name(self) -> str:
        """Alias for identifier for backward compatibility."""
        return self.identifier

    def on_event(self, *args, **kwargs) -> Any:
        """Handle an event. Override in subclasses."""
        return None

    def degrade(self, amount: float) -> None:
        """Increase ablative wear by the specified amount (clamped to [0, 1]).

        Args:
            amount: The ablation increment (e.g., 0.1 for 10% more wear).
        """
        self.ablative = min(1.0, self.ablative + amount)

    def repair(self, amount: float) -> None:
        """Decrease ablative wear by the specified amount (clamped to [0, 1]).

        Args:
            amount: The repair decrement (e.g., 0.05 for 5% wear reduction).
        """
        self.ablative = max(0.0, self.ablative - amount)

    def set_reliability(self, value: float) -> None:
        """Set reliability, clamped to [0, 10]."""
        self.reliability = max(0.0, min(10.0, value))

    def is_functional(self) -> bool:
        """Return True if the entity is functional (reliability > 0 and not fully ablated)."""
        return self.reliability > 0.0 and self.ablative < 1.0

    def effectiveness(self) -> float:
        """Return a combined effectiveness metric (0-1) based on reliability and ablation.

        Effectiveness = (reliability / 10.0) * (1 - ablative)
        """
        return (self.reliability / 10.0) * (1.0 - self.ablative)
