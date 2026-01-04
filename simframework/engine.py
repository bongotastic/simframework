"""Minimal simulation engine coordinating entities, systems/agents and the scheduler.

This engine provides simple registries for simulation participants (entities),
as well as system and agent instances. Registries allow O(1) lookup by id,
convenience helpers to schedule events on behalf of a specific system/agent,
and basic lifecycle operations (add/get/remove).
"""
from __future__ import annotations

import datetime
from typing import Dict, Optional, Any
import math
import random

from .scheduler import Scheduler
from .entity import Entity
from .event import Event


class SimulationEngine:
    def __init__(self, start_time: Optional[datetime.datetime] = None):
        """Create an engine with an attached `Scheduler` and empty registries.

        Args:
            start_time: Optional simulation start time (datetime). If omitted,
                Scheduler will use its default of now().
        """
        self.scheduler = Scheduler(start_time=start_time)
        # Default shape parameter for log-logistic calculations
        self.default_beta: float = 10.0
        # Entities are application-level participants (e.g., sensors, actors)
        self.entities: Dict[str, Entity] = {}
        # Internal counter to produce unique entity ids when none provided
        self._entity_counter: int = 0
        # Inception time (simulation start) stored for external access
        self.inception_time: Optional[datetime.datetime] = self.scheduler.now

        # Load domain and processes (if available). Accept explicit paths via
        # constructor parameters in the future; by default attempt to load the
        # Demesne simulation's domain and processes if present in the workspace.
        from pathlib import Path
        try:
            from .scope import Domain
            from .process import Process
            import yaml
        except Exception:
            Domain = None
            Process = None
            yaml = None

        self.domain = None
        self.processes: Dict[str, "Process"] = {}

        # Try to find the Demesne domain files relative to the repo root
        repo_root = Path.cwd()
        domain_candidate = repo_root / "simulations" / "Demesne" / "domain.yaml"
        processes_candidate = repo_root / "simulations" / "Demesne" / "domain_processes.yaml"

        if Domain is not None and domain_candidate.exists():
            try:
                self.domain = Domain.from_yaml(str(domain_candidate))
            except Exception:
                self.domain = None

        if Process is not None and yaml is not None and processes_candidate.exists():
            try:
                with open(processes_candidate, "r") as fh:
                    pd = yaml.safe_load(fh)
                for proc_dict in pd.get("processes", []):
                    try:
                        proc = Process.from_yaml_dict(proc_dict)
                        self.processes[proc.path] = proc
                    except Exception:
                        # Best-effort: skip malformed process entries
                        continue
            except Exception:
                # Ignore process load errors and continue
                pass


    # --- entity registry ---
    def add_entity(self, entity: Entity, entity_id: Optional[str] = None) -> str:
        """Register an `Entity` and return its id.

        If `entity_id` is provided, it is used and a ValueError is raised on
        collision. If omitted, the engine will generate a unique id by
        appending an internal counter to `entity.name` (or to the literal
        'entity' when name is missing). Generated ids will never raise an
        exception on collision — the counter is incremented until a unique id
        is produced.
        """
        if entity_id:
            eid = entity_id
            if eid in self.entities:
                raise ValueError(f"entity id already registered: {eid}")
            self.entities[eid] = entity
            return eid

        # Generate a unique id based on the entity's name and an internal counter
        base = getattr(entity, "name", None) or "entity"
        # Loop until we find a free id; this is deterministic and will always
        # terminate because the counter increases on each attempt.
        while True:
            eid = f"{base}_{self._entity_counter}"
            self._entity_counter += 1
            if eid not in self.entities:
                self.entities[eid] = entity
                return eid

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def remove_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.pop(entity_id, None)
    # (System/Agent registries have been removed — use `Entity` and `Person`)

    # --- scheduling helpers ---
    def schedule_for_entity(self, entity_id: str, delay: float, event: Optional[Event] = None, **data) -> tuple[datetime.datetime, int]:
        """Schedule an event anchored to an `Entity` with id `entity_id`.

        The scheduled `Event` will have its `.system` attribute set to the
        corresponding `Entity` instance for backward compatibility with
        existing Event consumers that expect a `.system` attribute.
        If `event` is not provided, a new Event is created using `data`.
        """
        entity = self.get_entity(entity_id)
        if entity is None:
            raise KeyError(entity_id)
        if event is None:
            event = Event(data=data)
        event.system = entity
        return self.scheduler.schedule(delay, event=event, **data)

    def set_inception_time(self, inception: datetime.datetime) -> None:
        """Set the simulation inception time and update the scheduler's now.

        Args:
            inception: a datetime.datetime to use as the simulation start time.
        """
        if not isinstance(inception, datetime.datetime):
            raise TypeError("inception must be a datetime.datetime")
        self.inception_time = inception
        # Update scheduler's now property (Scheduler enforces datetime type)
        if hasattr(self, "scheduler") and self.scheduler is not None:
            try:
                self.scheduler.now = inception
            except Exception:
                # Best-effort: do not raise if scheduler refuses to update
                pass

    def get_inception_time(self) -> Optional[datetime.datetime]:
        """Return the configured inception time or the scheduler's current time."""
        if self.inception_time is not None:
            return self.inception_time
        if hasattr(self, "scheduler") and self.scheduler is not None:
            return self.scheduler.now
        return None

    def run(self, until: Optional[datetime.datetime] = None) -> None:
        self.scheduler.run(until=until)

    def get_process(self, identifier: str) -> Optional["Process"]:
        """Retrieve a loaded Process by path or name.

        The lookup strategy is (in order):
        1. Exact path key in `self.processes` (e.g., "process/cultivation/sowing").
        2. Exact `Process.name` match.
        3. Path suffix match (e.g., "sowing" -> matches path ending with "sowing").
        4. Case-insensitive substring match against path or name.

        Returns the first matching `Process` or None if not found.
        """
        if not identifier:
            return None

        # 1) Exact path
        if identifier in self.processes:
            return self.processes[identifier]

        # 2) Exact name match
        for proc in self.processes.values():
            try:
                if proc.name == identifier:
                    return proc
            except Exception:
                continue

        # 3) Path suffix match
        for proc in self.processes.values():
            try:
                if proc.path.endswith(identifier):
                    return proc
            except Exception:
                continue

        # 4) Case-insensitive substring match
        ident_low = identifier.lower()
        for proc in self.processes.values():
            try:
                if ident_low in proc.name.lower() or ident_low in proc.path.lower():
                    return proc
            except Exception:
                continue

        return None

    def determine_spoilage_probability(self, age: float, median_time: float, beta: float = 10.0) -> float:
        """Return the log-logistic cumulative failure probability at `age`.

        Uses the standard log-logistic CDF where `median_time` is the scale
        parameter (the time at which the CDF equals 0.5) and `beta` is the
        shape parameter. The CDF is:

            F(t) = 1 / (1 + (median_time / t) ** beta)

        Args:
            age: Age or time to evaluate (must be >= 0).
            median_time: Median time (scale parameter), must be > 0.
            beta: Shape parameter (default 10.0).

        Returns:
            A float in [0.0, 1.0] giving the probability of failure by `age`.
        """
        try:
            t = float(age)
            a = float(median_time)
            b = float(beta)
        except Exception:
            raise TypeError("age, median_time and beta must be numeric")

        if t <= 0.0:
            return 0.0
        if a <= 0.0:
            raise ValueError("median_time must be > 0")
        if b <= 0.0:
            raise ValueError("beta must be > 0")

        # Compute (median / t) ** beta in a numerically stable way
        ratio = a / t
        # If ratio is extremely large, (ratio ** b) may overflow; handle large/small cases
        try:
            power = math.pow(ratio, b)
        except OverflowError:
            # ratio ** b is effectively infinite -> F(t) -> 0
            return 0.0

        return 1.0 / (1.0 + power)

    def determine_spoilage(self, age: float, median_time: float, beta: Optional[float] = None) -> bool:
        """Return True if an item of given `age` spoils, using log-logistic sampling.

        Args:
            age: Age or time to evaluate (must be >= 0).
            median_time: Median time (scale parameter), must be > 0.
            beta: Optional shape parameter. If omitted, uses the engine's
                `default_beta` value.

        Returns:
            True if a sampled uniform random number is less than the
            log-logistic CDF at `age`, False otherwise.
        """
        b = float(beta) if beta is not None else float(self.default_beta)
        p = self.determine_spoilage_probability(age, median_time, b)
        return random.random() < p

    def determine_breakage_probability(self, deltatime: float, mtbf: float) -> float:
        """Calculate the probability of mechanical failure over `deltatime`.

        Uses an exponential failure model derived from an assumed constant
        failure rate where `mtbf` is the mean time between failures. The
        probability of at least one failure in time interval Δ is:

            P = 1 - exp(-Δ / MTBF)

        Args:
            deltatime: Time interval over which to calculate failure probability (>= 0).
            mtbf: Mean time between failures (MTBF) in same units as `deltatime` (> 0).

        Returns:
            Probability in [0.0, 1.0].
        """
        try:
            dt = float(deltatime)
            m = float(mtbf)
        except Exception:
            raise TypeError("deltatime and mtbf must be numeric")

        if dt <= 0.0:
            return 0.0
        if m <= 0.0:
            raise ValueError("mtbf must be > 0")

        # Exponential model: P = 1 - exp(-lambda * dt) where lambda = 1/mtbf
        rate = 1.0 / m
        # Use math.exp for numerical stability
        return 1.0 - math.exp(-rate * dt)

    def determine_breakage(self, deltatime: float, mtbf: float) -> bool:
        """Return True if a random draw indicates breakage over `deltatime`.

        Samples a uniform random value and returns True when it's less than
        the breakage probability computed by `determine_breakage_probability`.
        """
        p = self.determine_breakage_probability(deltatime, mtbf)
        return random.random() < p

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

        print("=" * 90)
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
        print("=" * 90 + "\n")