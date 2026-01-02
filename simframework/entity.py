"""Basic entity abstraction for simulation participants."""
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, field
import math
from copy import deepcopy


@dataclass
class Entity:
    """An entity representing a physical object in the simulation.

    Entities model tools, containers, inputs, outputs, and other tangible objects.
    Each entity has:
    - identifier: A taxonomy-based identifier (e.g., Scope path or unique name)
    - reliability: A measure of functionality (0-10 scale)
    - volume_liters: Volume in liters (float)
    - mass_kg: Mass in kilograms (float)
    - ablative: A measure of wear/degradation (0-1 scale, where 1 = fully degraded)
    """

    identifier: str  # From domain taxonomy (e.g., "environment/temperature/sensor")
    reliability: int = 10  # Integer 0-10 scale (10 = fully reliable, 0 = non-functional)
    volume_liters: float = 0.0  # Volume in liters
    mass_kg: float = 0.0  # Mass in kilograms
    ablative: float = 0.0  # 0-1 scale (0 = no degradation, 1 = completely ablated)
    # contents: taxonomy name -> list of Entity instances
    contents: Dict[str, List["Entity"]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate reliability (int), volume, mass, and ablative values are within bounds and types."""
        if not isinstance(self.reliability, int) or not (0 <= self.reliability <= 10):
            raise ValueError(f"reliability must be an int between 0 and 10; got {self.reliability}")
        if not isinstance(self.volume_liters, (int, float)) or self.volume_liters < 0.0:
            raise ValueError(f"volume_liters must be a non-negative number; got {self.volume_liters}")
        if not isinstance(self.mass_kg, (int, float)) or self.mass_kg < 0.0:
            raise ValueError(f"mass_kg must be a non-negative number; got {self.mass_kg}")
        if not 0.0 <= self.ablative <= 1.0:
            raise ValueError(f"ablative must be between 0 and 1; got {self.ablative}")

    def add_to_container(self, entity_or_list: Union["Entity", List["Entity"]], quantity: int = 1) -> None:
        """Add an Entity or list of Entities into this entity's contents.

        The contents dict maps taxonomy name (entity.identifier) -> list of Entity instances.

        Args:
            entity_or_list: An Entity instance or list of Entity instances to add.
            quantity: If entity_or_list is a single Entity, add `quantity` copies of it (default 1).
                     If a list is provided, quantity is ignored and all items are added as-is.
        """
        if isinstance(entity_or_list, Entity):
            # Single entity: replicate it by quantity
            for _ in range(quantity):
                key = entity_or_list.identifier
                self.contents.setdefault(key, []).append(deepcopy(entity_or_list))
        else:
            # List of entities: add all, quantity ignored
            items = list(entity_or_list)
            for ent in items:
                key = ent.identifier
                self.contents.setdefault(key, []).append(ent)

    def query_container(self, name: str) -> List["Entity"]:
        """Return a list of contained Entity instances matching taxonomy name."""
        return list(self.contents.get(name, []))

    def remove_from_container(self, name: str, count: int = 1) -> List["Entity"]:
        """Remove contained Entity instances by taxonomy name.

        Args:
            name: The taxonomy name (identifier) to remove from.
            count: Number of Entity instances to remove (default 1).

        Returns:
            A list of Entity instances that were removed.
            If fewer than count instances exist, removes as many as possible.
        """
        removed: List[Entity] = []
        if name not in self.contents:
            return removed

        bucket = self.contents[name]
        # Remove up to count instances
        for _ in range(min(count, len(bucket))):
            removed.append(bucket.pop(0))
        
        # Remove key if bucket is now empty
        if not bucket:
            del self.contents[name]
        
        return removed

    @property
    def name(self) -> str:
        """Alias for identifier for backward compatibility."""
        return self.identifier

    def on_event(self, *args, **kwargs) -> Any:
        """Handle an event. Override in subclasses."""
        return None

    def ablate(self, amount: float) -> None:
        """Increase ablative wear by the specified amount (clamped to [0, 1]).

        Args:
            amount: The ablation increment (e.g., 0.1 for 10% more wear).
        """
        self.ablative = min(1.0, self.ablative + amount)

    def reliability_test(self) -> bool:
        """Perform a reliability test based on the current reliability score.

        Returns:
            True if the entity passes the reliability test, False otherwise.
        """
        import random

        roll = random.randint(1, 10)
        return roll <= self.reliability
    
    def is_functional(self) -> bool:
        """Check if the entity is functional based on its reliability and ablative state.

        Returns:
            True if the entity is functional, False otherwise.
        """
        return self.reliability > 0 and self.ablative < 1.0