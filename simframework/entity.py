"""Basic entity abstraction for simulation participants."""
from typing import Any, Optional, Dict, List, Union, Tuple
from dataclasses import dataclass, field
import datetime
import math
from copy import deepcopy
from .scope import Scope


@dataclass
class Entity:
    """An entity representing a physical object in the simulation.

    Entities model tools, containers, inputs, outputs, and other tangible objects.
    Each entity has:
    - identifier: A taxonomy-based identifier (e.g., Scope path or unique name)
    - volume_liters: Volume in liters (float)
    - mass_kg: Mass in kilograms (float)
    """
    # Unique identifier (string key). Default empty so engine can assign one.
    identifier: str = field(default="")

    # semantic definition
    # `essence` describes what the entity is (taxonomy); may be a Scope or a path string
    essence: Optional[Union[Scope, str]] = None
    # properties: maps taxonomy full-path (string) -> arbitrary value (may be Scope)
    properties: Dict[str, Any] = field(default_factory=dict)
    # material: optional taxonomy scope describing material/composition
    material: Optional[Union[str, Scope]] = None

    # physical definition
    volume_liters: float = 0.0  # Volume in liters
    mass_kg: float = 0.0  # Mass in kilograms
    # contents: taxonomy name -> list of Entity instances
    contents: Dict[str, List["Entity"]] = field(default_factory=dict)
    # internal clock stored as a datetime; initialized to epoch (0)
    internal_clock: datetime.datetime = field(default_factory=lambda: datetime.datetime.fromtimestamp(0))
    

    def __post_init__(self) -> None:
        """Validate volume, mass, properties, and internal clock types/values."""
        if not isinstance(self.volume_liters, (int, float)) or self.volume_liters < 0.0:
            raise ValueError(f"volume_liters must be a non-negative number; got {self.volume_liters}")
        if not isinstance(self.mass_kg, (int, float)) or self.mass_kg < 0.0:
            raise ValueError(f"mass_kg must be a non-negative number; got {self.mass_kg}")

        # Validate identifier is a string (unique key)
        if not isinstance(self.identifier, str):
            raise TypeError("identifier must be a string")

        # Validate essence is either None, a string path, or a Scope
        if getattr(self, "essence", None) is not None and not isinstance(self.essence, (str, Scope)):
            raise TypeError("essence must be a Scope, a taxonomy path string, or None")

        # Validate properties dict keys are strings (full-path keys)
        if not isinstance(self.properties, dict):
            raise TypeError("properties must be a dict mapping strings to values")
        for k in list(self.properties.keys()):
            if not isinstance(k, str):
                raise TypeError(f"property keys must be strings; got {type(k)}")

        # Validate material is either None, a string path, or a Scope
        if self.material is not None and not isinstance(self.material, (str, Scope)):
            raise TypeError("material must be a taxonomy path string, Scope, or None")

        # Validate internal clock is a datetime
        if not isinstance(self.internal_clock, datetime.datetime):
            raise TypeError("internal_clock must be a datetime.datetime")

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
                key = entity_or_list.essence.full_path() if isinstance(entity_or_list.essence, Scope) else entity_or_list.essence
                self.contents.setdefault(key, []).append(deepcopy(entity_or_list))
        else:
            # List of entities: add all, quantity ignored
            items = list(entity_or_list)
            for ent in items:
                key = ent.essence.full_path() if isinstance(ent.essence, Scope) else ent.essence
                self.contents.setdefault(key, []).append(ent)

    def add_content(self, entity: "Entity") -> None:
        """Add an Entity into this entity's contents keyed by the entity's identifier.

        The stored value is the Entity instance itself (no deepcopy). The key used
        is `entity.identifier` (must be a non-empty string).
        """
        if not isinstance(entity, Entity):
            raise TypeError("entity must be an Entity")

        key = entity.identifier
        if not isinstance(key, str) or key == "":
            raise ValueError("entity.identifier must be a non-empty string")

        # Append the instance to the bucket for this identifier
        self.contents.setdefault(key, []).append(entity)

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
        raise AttributeError("ablative support was removed; ablate() is no longer available")

    def reliability_test(self) -> bool:
        """Perform a reliability test based on the current reliability score.

        Returns:
            True if the entity passes the reliability test, False otherwise.
        """
        raise AttributeError("reliability support was removed; reliability_test() is no longer available")
    
    def is_functional(self) -> bool:
        """Check basic functional state based on mass/volume/properties presence.

        This is a simplified placeholder replacing prior reliability/ablative checks.
        Returns True when the entity has non-zero mass or volume or any properties set.
        """
        return bool(self.properties) or (self.mass_kg > 0.0) or (self.volume_liters > 0.0)

    def set_property(self, key: str, value: Any) -> None:
        """Set a property on this entity.

        Args:
            key: property name (must be a string)
            value: any JSON-serializable or domain-specific value
        """
        if not isinstance(key, str):
            raise TypeError("property key must be a string")
        self.properties[key] = value

    def set_internal_clock(self, dt: datetime.datetime) -> None:
        """Set the entity's internal clock (datetime)."""
        if not isinstance(dt, datetime.datetime):
            raise TypeError("internal clock must be a datetime.datetime")
        self.internal_clock = dt

    def get_internal_clock(self) -> datetime.datetime:
        """Return the entity's internal clock as a datetime."""
        return self.internal_clock

    def unset_property(self, key: str) -> None:
        """Remove a property from this entity if present."""
        if not isinstance(key, str):
            raise TypeError("property key must be a string")
        self.properties.pop(key, None)

    def has_property(self, key: str) -> bool:
        """Return True if the entity has a property named `key`."""
        if not isinstance(key, str):
            raise TypeError("property key must be a string")
        return key in self.properties


@dataclass
class Person(Entity):
    """A person in the simulation with skill/attribute levels.

    `attributes` maps taxonomy identifier strings (e.g. "attributes/skill/smithing")
    to integer levels (e.g. 0..10). Validation ensures keys are strings and values
    are non-negative integers.
    """

    attributes: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate base Entity fields first
        super().__post_init__()

        if not isinstance(self.attributes, dict):
            raise TypeError("attributes must be a dict mapping taxonomy strings to integer levels")

        for k, v in list(self.attributes.items()):
            if not isinstance(k, str):
                raise TypeError(f"attribute keys must be strings (taxonomy ids); got {type(k)}")
            if not isinstance(v, int) or v < 0:
                raise ValueError(f"attribute levels must be non-negative integers; got {v} for {k}")

    def get_attribute(self, key: str) -> int:
        """Return the integer level for `key`, or 0 if not present."""
        return int(self.attributes.get(key, 0))

    def set_attribute(self, key: str, level: int) -> None:
        """Set the attribute `key` to integer `level` (must be non-negative)."""
        if not isinstance(key, str):
            raise TypeError("attribute key must be a string")
        if not isinstance(level, int) or level < 0:
            raise ValueError("attribute level must be a non-negative integer")
        self.attributes[key] = level


@dataclass
class Location(Entity):
    """A physical location entity with traversal and adjacency information.

    Attributes:
        traversal_meter: mean intra-location travel distance in meters
        adjacency_list: list of tuples (Entity, distance_meters) representing
                        adjacent locations/entities and the distance to them.
    """

    traversal_meter: float = 0.0
    adjacency_list: List[Tuple["Entity", float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Run base validation
        super().__post_init__()

        if not isinstance(self.traversal_meter, (int, float)) or self.traversal_meter < 0.0:
            raise ValueError("traversal_meter must be a non-negative number")

        # Validate adjacency entries
        if not isinstance(self.adjacency_list, list):
            raise TypeError("adjacency_list must be a list of (Entity, distance) tuples")
        for item in list(self.adjacency_list):
            if not (isinstance(item, tuple) and len(item) == 2):
                raise TypeError("each adjacency must be a (Entity, distance) tuple")
            ent, dist = item
            if not isinstance(dist, (int, float)) or dist < 0.0:
                raise ValueError("adjacency distance must be a non-negative number")
            # allow forward-referenced Entity; perform a weak runtime check
            if not hasattr(ent, "identifier"):
                raise TypeError("adjacency entity must be an Entity-like object")

    def add_adjacent(self, entity: "Entity", distance_m: float) -> None:
        """Add an adjacent entity with the given distance in meters."""
        if not isinstance(distance_m, (int, float)) or distance_m < 0.0:
            raise ValueError("distance_m must be a non-negative number")
        self.adjacency_list.append((entity, float(distance_m)))

    def remove_adjacent(self, entity: "Entity") -> None:
        """Remove adjacency entries referring to `entity`."""
        self.adjacency_list = [(e, d) for (e, d) in self.adjacency_list if e is not entity]

    def neighbors(self) -> List["Entity"]:
        """Return adjacent entities (shallow list)."""
        return [e for (e, _) in self.adjacency_list]

    def get_distance(self, entity: "Entity") -> Optional[float]:
        """Return distance to `entity` if present, else None."""
        for e, d in self.adjacency_list:
            if e is entity:
                return d
        return None