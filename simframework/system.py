"""System templates and instances for simulation components.

A SystemTemplate describes a system archetype (e.g., a machine, an organization).
`SystemTemplate.instantiate()` creates a `SystemInstance` which can hold runtime
state, property overrides, and child systems. Instances are hashable identifiers
that can be attached to `Event` objects for filtering.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
import datetime


@dataclass
class ProcessIO:
    """Input or output for a process: a kind (from taxonomy) with quantity and rate interval."""

    kind: Any  # Typically a Scope from taxonomy, but can be any hashable identifier
    quantity: float  # Base amount per interval (e.g., 10.0)
    interval: datetime.timedelta  # Rate interval (e.g., per hour)

    def quantity_per_second(self) -> float:
        """Return the rate in units per second."""
        total_seconds = self.interval.total_seconds()
        if total_seconds <= 0:
            return 0.0
        return self.quantity / total_seconds


@dataclass
class Process:
    """A process: transforms inputs to outputs at a specified efficiency over time.

    A process can require one or more agents to execute. Efficiency represents the
    fraction of input energy/material that is converted to useful output (0.0 to 1.0).
    """

    name: str
    inputs: List[ProcessIO] = field(default_factory=list)
    outputs: List[ProcessIO] = field(default_factory=list)
    efficiency: float = 1.0  # Default: no loss (0.0 to 1.0)
    required_agents: List[str] = field(default_factory=list)  # Agent ids or names


@dataclass
class Store:
    """A store of some resource: a kind (from taxonomy) with current quantity."""

    kind: Any  # Typically a Scope, but can be any hashable identifier
    quantity: float = 0.0


@dataclass
class PropertySpec:
    """Definition of a system property."""

    default: Any = None
    transitive: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: Any) -> "PropertySpec":
        """Create a PropertySpec from a plain value or dict."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict) and ("default" in value or "transitive" in value or "metadata" in value):
            return cls(
                default=value.get("default"),
                transitive=bool(value.get("transitive", False)),
                metadata=value.get("metadata", {}) or {},
            )
        return cls(default=value, transitive=False)


@dataclass
class SystemTemplate:
    """Template describing a system archetype."""

    name: str
    properties: Dict[str, PropertySpec] = field(default_factory=dict)
    children: List["SystemTemplate"] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    is_location: bool = False

    def __post_init__(self) -> None:
        # Normalize property definitions for consistent access
        self.properties = {k: PropertySpec.from_value(v) for k, v in (self.properties or {}).items()}
        # Normalize labels to list of strings
        self.labels = list(self.labels or [])
        self.is_location = bool(self.is_location)

    def add_child(self, child: "SystemTemplate") -> None:
        """Attach a child template to this template."""
        self.children.append(child)

    def property_spec(self, name: str) -> Optional[PropertySpec]:
        return self.properties.get(name)

    def instantiate(
        self,
        instance_id: Optional[str] = None,
        *,
        parent: Optional["SystemInstance"] = None,
        overrides: Optional[Dict[str, Any]] = None,
        include_children: bool = True,
        **state: Any,
    ) -> "SystemInstance":
        """Create a SystemInstance from this template.

        Args:
            instance_id: Optional explicit id; defaults to `<template.name>-inst`.
            parent: Optional parent SystemInstance (to build hierarchies).
            overrides: Property overrides for this instance.
            include_children: When True, child templates are instantiated with their defaults.
            **state: Additional property overrides (shorthand instead of `overrides`).
        """
        combined_overrides = dict(overrides or {})
        combined_overrides.update(state)
        inst = SystemInstance(
            template=self,
            id=instance_id or f"{self.name}-inst",
            parent=parent,
            overrides=combined_overrides,
            labels=list(self.labels),
            is_location=self.is_location,
        )
        if include_children:
            for child_template in self.children:
                child_inst = child_template.instantiate(parent=inst)
                inst.add_child(child_inst)
        return inst


@dataclass
class SystemInstance:
    """Runtime instance of a system template."""

    template: SystemTemplate
    id: str
    parent: Optional["SystemInstance"] = None
    overrides: Dict[str, Any] = field(default_factory=dict)
    children: List["SystemInstance"] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    is_location: bool = False
    processes: List[Process] = field(default_factory=list)
    stores: List[Store] = field(default_factory=list)

    def add_child(self, child: "SystemInstance") -> None:
        """Attach an existing child instance."""
        child.parent = self
        self.children.append(child)

    def add_process(self, process: Process) -> None:
        """Add a process to this system."""
        self.processes.append(process)

    def aggregate_processes(self, include_children: bool = True) -> List[Process]:
        """Return all processes in this system (and optionally all children recursively)."""
        result = list(self.processes)
        if include_children:
            for child in self.children:
                result.extend(child.aggregate_processes(include_children=True))
        return result

    def aggregate_stores(self, include_children: bool = True) -> Dict[Any, float]:
        """Return aggregated stores as {kind: total_quantity} (recursively if include_children)."""
        result: Dict[Any, float] = {}
        # Add this system's stores
        for store in self.stores:
            result[store.kind] = result.get(store.kind, 0.0) + store.quantity
        # Add children's stores recursively
        if include_children:
            for child in self.children:
                child_stores = child.aggregate_stores(include_children=True)
                for kind, qty in child_stores.items():
                    result[kind] = result.get(kind, 0.0) + qty
        return result

    def add_store(self, kind: Any, quantity: float = 0.0) -> None:
        """Add or update a store of a given kind."""
        for store in self.stores:
            if store.kind == kind:
                store.quantity += quantity
                return
        self.stores.append(Store(kind=kind, quantity=quantity))

    def get_store(self, kind: Any) -> Optional[Store]:
        """Retrieve a store by kind."""
        for store in self.stores:
            if store.kind == kind:
                return store
        return None

    def execute_process(self, process: Process, duration: datetime.timedelta) -> bool:
        """Execute a process over a duration, consuming inputs and producing outputs.

        Returns True if execution succeeded, False if insufficient inputs.

        The process:
        1. Checks if all required inputs are available in stores
        2. Consumes inputs at the specified rate
        3. Produces outputs at (input * efficiency) rate
        """
        # Calculate total quantities needed/produced for the duration
        duration_seconds = duration.total_seconds()
        if duration_seconds <= 0:
            return False

        # Check availability of all inputs
        for io in process.inputs:
            rate_per_sec = io.quantity_per_second()
            needed = rate_per_sec * duration_seconds
            store = self.get_store(io.kind)
            if store is None or store.quantity < needed:
                return False  # Insufficient input

        # Consume inputs
        for io in process.inputs:
            rate_per_sec = io.quantity_per_second()
            consumed = rate_per_sec * duration_seconds
            store = self.get_store(io.kind)
            if store is not None:
                store.quantity -= consumed

        # Produce outputs (applying efficiency)
        for io in process.outputs:
            rate_per_sec = io.quantity_per_second()
            produced = (rate_per_sec * duration_seconds) * process.efficiency
            self.add_store(io.kind, produced)

        return True

    def iter_ancestors(self) -> Iterable["SystemInstance"]:
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    def path(self) -> str:
        """Return a hierarchical identifier for this instance."""
        parts = [self.id]
        parent = self.parent
        while parent is not None:
            parts.append(parent.id)
            parent = parent.parent
        return "/".join(reversed(parts))

    def get_property(self, name: str, default: Any = None) -> Any:
        """Resolve a property value using overrides, transitivity, and defaults."""
        spec = self.template.property_spec(name)
        sentinel = object()
        local_value = self.overrides.get(name, sentinel)

        if local_value is not sentinel:
            return local_value

        # If property is defined and transitive, check ancestors
        if spec is not None and spec.transitive:
            for ancestor in self.iter_ancestors():
                ancestor_val = ancestor.get_property(name, sentinel)
                if ancestor_val is not sentinel:
                    return ancestor_val

        # If property is not defined locally but an ancestor may define a transitive property spec
        if spec is None:
            for ancestor in self.iter_ancestors():
                ancestor_spec = ancestor.template.property_spec(name)
                if ancestor_spec is not None and ancestor_spec.transitive:
                    ancestor_val = ancestor.get_property(name, sentinel)
                    if ancestor_val is not sentinel:
                        return ancestor_val

        if spec is not None:
            return spec.default

        return default

    @property
    def resolved_properties(self) -> Dict[str, Any]:
        """Return a merged view of properties available to this instance."""
        result: Dict[str, Any] = {}
        # Start with ancestor transitive properties
        for ancestor in reversed(list(self.iter_ancestors())):
            for key, spec in ancestor.template.properties.items():
                if not spec.transitive:
                    continue
                val = ancestor.get_property(key, None)
                if val is not None:
                    result[key] = val
        # Apply this template's defaults
        for key, spec in self.template.properties.items():
            result.setdefault(key, spec.default)
        # Apply overrides last
        result.update(self.overrides)
        return result

    def set_property(self, name: str, value: Any) -> None:
        """Set or override a property value on this instance."""
        self.overrides[name] = value

    def event_payload(self, **kwargs: Any) -> Dict[str, Any]:
        """Return a payload dictionary tagged with this system for convenience."""
        data = dict(kwargs)
        data["system"] = self.path()
        return data

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"SystemInstance(id={self.id!r}, template={self.template.name!r})"

    def __hash__(self) -> int:
        return hash((self.template.name, self.id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SystemInstance):
            return False
        return (self.template.name, self.id) == (other.template.name, other.id)


__all__ = ["PropertySpec", "SystemTemplate", "SystemInstance", "Process", "ProcessIO", "Store", "Agent", "AgentTemplate"]


@dataclass
class Agent(SystemInstance):
    """Agent: a specialized SystemInstance capable of perception, goals, and tasks.

    Agents are primarily runtime actors that can perceive `Entity` objects
    via the `SimulationEngine`, interact with other systems (by scheduling
    events on their behalf), and maintain a list of goals and a current task
    (represented as a `Scope`).
    """

    goals: List[str] = field(default_factory=list)
    current_task: Optional["Scope"] = None
    # Agent's current location within the system hierarchy (e.g., a module instance)
    location: Optional["SystemInstance"] = None

    def add_goal(self, goal: str) -> None:
        self.goals.append(goal)

    def pop_goal(self) -> Optional[str]:
        if not self.goals:
            return None
        return self.goals.pop(0)

    def assign_task(self, task: "Scope") -> None:
        self.current_task = task

    def set_location(self, location: "SystemInstance") -> None:
        """Set the agent's current location to a SystemInstance (e.g., module)."""
        self.location = location

    def clear_location(self) -> None:
        """Clear the agent's current location."""
        self.location = None

    def perceive_entities(self, engine: "SimulationEngine", predicate: Optional[callable] = None):
        """Return entities visible to this agent.

        If `predicate` is provided it will be applied to each `Entity` and
        only those for which it returns True will be returned.

        When the agent has a `location` set and `predicate` is None, perception
        defaults to entities whose `location` attribute equals the agent's
        location. This provides a simple location-based sensing model.
        """
        # Import locally to avoid circular imports at module import time
        from .entity import Entity  # type: ignore
        visible = []
        for ent in engine.entities.values():
            if not isinstance(ent, Entity):
                continue
            if predicate is not None:
                if predicate(ent):
                    visible.append(ent)
                continue
            # Default behaviour: if agent has a location, only show co-located entities
            if self.location is not None:
                if getattr(ent, "location", None) == self.location:
                    visible.append(ent)
                continue
            visible.append(ent)
        return visible

    def interact_with_system(self, engine: "SimulationEngine", system_id: str, delay: float, callback, *args, **kwargs):
        """Convenience wrapper allowing an agent to schedule work on a system."""
        return engine.schedule_for_system(system_id, delay, callback, *args, **kwargs)


class AgentTemplate(SystemTemplate):
    """Template for creating Agent instances from a template.

    Behaves like `SystemTemplate.instantiate()` but returns `Agent` instances
    (which extend `SystemInstance`) when instantiated. Child templates that are
    `AgentTemplate` will produce `Agent` children; other child templates will
    produce `SystemInstance` children as usual.
    """

    def instantiate(
        self,
        instance_id: Optional[str] = None,
        *,
        parent: Optional[SystemInstance] = None,
        overrides: Optional[Dict[str, Any]] = None,
        include_children: bool = True,
        **state: Any,
    ) -> "Agent":
        combined_overrides = dict(overrides or {})
        combined_overrides.update(state)
        inst = Agent(
            template=self,
            id=instance_id or f"{self.name}-inst",
            parent=parent,
            overrides=combined_overrides,
            labels=list(self.labels),
            is_location=self.is_location,
        )
        if include_children:
            for child_template in self.children:
                # Preserve specialized agent children when templates are AgentTemplate
                if isinstance(child_template, AgentTemplate):
                    child_inst = child_template.instantiate(parent=inst)
                else:
                    child_inst = child_template.instantiate(parent=inst)
                inst.add_child(child_inst)
        return inst
