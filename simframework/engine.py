"""Minimal simulation engine coordinating entities, systems/agents and the scheduler.

This engine provides simple registries for simulation participants (entities),
as well as system and agent instances. Registries allow O(1) lookup by id,
convenience helpers to schedule events on behalf of a specific system/agent,
and basic lifecycle operations (add/get/remove).
"""
from __future__ import annotations

import datetime
from typing import Dict, Optional, Any

from .scheduler import Scheduler
from .entity import Entity
from .event import Event

try:
    # For type checking when package is used as a module
    from .system import SystemInstance
except Exception:  # pragma: no cover - fallback for tests
    from simframework.system import SystemInstance


class SimulationEngine:
    def __init__(self, start_time: Optional[datetime.datetime] = None):
        """Create an engine with an attached `Scheduler` and empty registries.

        Args:
            start_time: Optional simulation start time (datetime). If omitted,
                Scheduler will use its default of now().
        """
        self.scheduler = Scheduler(start_time=start_time)
        # Entities are application-level participants (e.g., sensors, actors)
        self.entities: Dict[str, Entity] = {}
        # Systems and agents are organized separately for clarity
        self.systems: Dict[str, SystemInstance] = {}
        self.agents: Dict[str, SystemInstance] = {}

    # --- entity registry ---
    def add_entity(self, entity: Entity, entity_id: Optional[str] = None) -> str:
        """Register an `Entity` and return its id.

        If `entity_id` is omitted, `entity.name` is used. Raises ValueError on
        id collision.
        """
        eid = entity_id or getattr(entity, "name", None)
        if not eid:
            raise ValueError("entity must have an id (or provide entity_id)")
        if eid in self.entities:
            raise ValueError(f"entity id already registered: {eid}")
        self.entities[eid] = entity
        return eid

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def remove_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.pop(entity_id, None)

    # --- system registry ---
    def add_system_instance(self, system: SystemInstance) -> str:
        """Register a SystemInstance by its `id`.

        Raises ValueError on id collision.
        """
        sid = system.id
        if sid in self.systems:
            raise ValueError(f"system id already registered: {sid}")
        self.systems[sid] = system
        return sid

    def get_system(self, system_id: str) -> Optional[SystemInstance]:
        return self.systems.get(system_id)

    def remove_system(self, system_id: str) -> Optional[SystemInstance]:
        return self.systems.pop(system_id, None)

    # --- agent registry (specialized systems) ---
    def add_agent(self, agent: SystemInstance) -> str:
        aid = agent.id
        if aid in self.agents:
            raise ValueError(f"agent id already registered: {aid}")
        self.agents[aid] = agent
        # Also register as a system for convenience
        if aid not in self.systems:
            self.systems[aid] = agent
        return aid

    def get_agent(self, agent_id: str) -> Optional[SystemInstance]:
        return self.agents.get(agent_id)

    def remove_agent(self, agent_id: str) -> Optional[SystemInstance]:
        self.agents.pop(agent_id, None)
        return self.systems.pop(agent_id, None)

    # --- scheduling helpers ---
    def schedule_for_system(self, system_id: str, delay: float, event: Optional[Event] = None, **data) -> tuple[datetime.datetime, int]:
        """Schedule an event anchored to the system with id `system_id`.

        The scheduled `Event` will have its `.system` set to the SystemInstance.
        If `event` is not provided, a new Event is created using `data`.
        """
        system = self.get_system(system_id)
        if system is None:
            raise KeyError(system_id)
        if event is None:
            event = Event(data=data)
        event.system = system
        return self.scheduler.schedule(delay, event=event, **data)

    def schedule_for_agent(self, agent_id: str, delay: float, event: Optional[Event] = None, **data) -> tuple[datetime.datetime, int]:
        """Schedule an event anchored to the agent with id `agent_id`.

        The scheduled `Event` will have its `.system` set to the SystemInstance (agent).
        If `event` is not provided, a new Event is created using `data`.
        """
        agent = self.get_agent(agent_id)
        if agent is None:
            raise KeyError(agent_id)
        if event is None:
            event = Event(data=data)
        event.system = agent
        return self.scheduler.schedule(delay, event=event, **data)

    def run(self, until: Optional[datetime.datetime] = None) -> None:
        self.scheduler.run(until=until)

    def print_status(self) -> None:
        """Print a compact status of the engine and the scheduler queue.

        Shows current scheduler time, number of events queued, next and last
        event times (if any), and a compact listing of queued events:
          ID | YYYY-MM-DD HH:MM:SS | scope | timespan
        """
        events = self.scheduler.peek_events()
        count = len(events)
        now = self.scheduler.now

        next_time = events[0][0] if events else None
        last_time = events[-1][0] if events else None

        print(f"Status at {now.strftime('%Y-%m-%d %H:%M:%S')}: {count} event(s) in queue")
        if next_time is not None:
            print(f"Next event: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last  event: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print("Events:")
        for run_at, event in events:
            # compact id retrieval
            eid = ""
            try:
                if isinstance(event.data, dict):
                    eid = event.data.get("event_id") or event.data.get("id") or ""
            except Exception:
                eid = ""

            # scope string
            scope = getattr(event, "scope", None)
            scope_str = scope.full_path() if scope is not None else ""

            timespan = getattr(event, "timespan", "")
            timespan_str = str(timespan) if timespan is not None else ""

            print(f"{str(eid):>3} | {run_at.strftime('%Y-%m-%d %H:%M:%S')} | {scope_str:30s} | {timespan_str}")
