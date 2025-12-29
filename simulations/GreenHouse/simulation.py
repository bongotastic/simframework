"""Greenhouse-specific simulation utilities

This module provides a small `GreenhouseSimulation` helper that inherits
from `SimulationEngine` and contains a focused place to write Greenhouse
simulation logic (instantiation, event scheduling, and event dispatch).

The class is intentionally lightweight: it demonstrates how to load the
`domain.yaml`, create the `Greenhouse` system instance, schedule a few
environment events (temperature, moisture, light), and run a simple
dispatch loop that calls small handler methods when events fire.

Extend or replace handler methods (`on_temperature_event`, etc.) to
implement richer greenhouse behaviors.
"""
from __future__ import annotations

from pathlib import Path
import datetime
from typing import Optional

from simframework.engine import SimulationEngine
from simframework.event import Event
from simframework.scope import Domain, Scope
from simframework.system import Process, SystemInstance
import logging

_logger = logging.getLogger(__name__)


class GreenhouseSimulation(SimulationEngine):
    """A small simulation wrapper for the GreenHouse domain.

    Usage example:
        sim = GreenhouseSimulation(start_time=..., domain_yaml="path/to/domain.yaml")
        sim.setup_greenhouse(instance_id="greenhouse-1")
        sim.schedule_environment_events()
        sim.run_and_dispatch()

    Handlers (`on_temperature_event`, `on_moisture_event`, `on_light_event`)
    are intentionally simple and should be replaced by domain-specific logic.
    """

    def __init__(self, start_time: Optional[datetime.datetime] = None, domain_yaml: Optional[str] = None):
        super().__init__(start_time=start_time)
        self.domain: Optional[Domain] = None
        self.greenhouse = None

        # Load domain if provided (fall back to local domain.yaml next to this file)
        yaml_path = None
        if domain_yaml:
            yaml_path = Path(domain_yaml)
        else:
            local = Path(__file__).resolve().parent / "domain.yaml"
            if local.exists():
                yaml_path = local

        if yaml_path is not None and yaml_path.exists():
            self.domain = Domain.from_yaml(str(yaml_path))

    def setup_greenhouse(self, instance_id: str = "greenhouse-1") -> Optional[object]:
        """Instantiate the Greenhouse system from the domain (if available).

        Returns the created SystemInstance or None if not found.
        """
        if self.domain is None:
            return None
        gh_tmpl = self.domain.get_system_template("Greenhouse")
        if gh_tmpl is None:
            return None
        self.greenhouse = gh_tmpl.instantiate(instance_id=instance_id)
        self.add_system_instance(self.greenhouse)
        return self.greenhouse

    # NOTE: `schedule_environment_events` was removed to encourage explicit event
    # scheduling via `scheduler.insert_event(...)`. This keeps the API minimal and
    # makes scheduling explicit in user code / tests.

    def dispatch_event(self, event: Event) -> None:
        """Route an Event to the appropriate handler based on its scope or data."""
        # Prefer an explicit `type` in payload, then fallback to scope name
        ev_type = event.data.get("type") if isinstance(event.data, dict) else None
        if ev_type is None and getattr(event, "scope", None) is not None:
            ev_type = event.scope.path() if isinstance(event.scope, Scope) else getattr(event.scope, "name", None)

        if ev_type is None:
            # Unknown event type: no-op
            return

        if ev_type.endswith("temperature") or ev_type == "environment/temperature":
            self.on_temperature_event(event)
        elif ev_type.endswith("moisture") or ev_type == "environment/moisture":
            self.on_moisture_event(event)
        elif ev_type.endswith("light") or ev_type == "environment/light":
            self.on_light_event(event)
        else:
            # Unknown; could be extended for more event types
            return

    
    def on_temperature_event(self, event: Event) -> None:
        """
        Modify the System's temperature
        Mode 1: set to a target value (if "set" property is present)
        Mode 2: alter by a delta value (if "alter" property is present)
        Mode 3: relative alter by a percentage (if "relative_alter" property is
        Mode 4: gradually change towards a target (if "gradual_change" property is present)
                Optionally, setting timespan controls the next temperature update (+/- 15%).
        
        :param self: Description
        :param event: Description
        :type event: Event
        """
        # Require an anchored system for temperature events. If none is provided
        # log an error and ignore the event (don't fall back to `self.greenhouse`).
        if getattr(event, "system", None) is None:
            _logger.error("temperature event received with no anchored system; ignoring event: %r", event)
            return

        target_system = event.system
        if target_system is None:
            return

        current = target_system.get_property("temperature", None)
        if current is None:
            return

        # Only modify temperature when the event explicitly specifies an action
        changed = False
        new_temp = None

        # Case 1: this event sets temperature to an absolute value
        if (event.get_property("set") is not None):
            new_temp = event.get_property("set")
            changed = True

        # Case 2: this event alters temperature by a delta (additive)
        elif (event.get_property("alter") is not None):
            new_temp = event.get_property("alter") + current
            changed = True

        # Case 3: this event applies a relative change (percentage)
        elif (event.get_property("relative_alter") is not None):
            new_temp = (1 + event.get_property("relative_alter")) * current
            changed = True

        # Case 4: gradually change in temperature and nerf when close enough
        elif (event.get_property("gradual_change") is not None):
            target = event.get_property("gradual_change")
            new_temp = current + (target - current) * 0.25 # Arbitrary 25% step toward target
            changed = True

            # Trigger the next event if the delta is more than 0.5 degrees away
            if abs(new_temp - target) > 0.5:
                # Schedule the next gradual-change event after the event.timespan
                next_event = Event(data=event.data.copy(), timespan=event.timespan)
                scope_obj = self.domain.get_scope("environment/temperature") if self.domain else None
                # Use the event.timespan (timedelta) as the trigger delay
                self.scheduler.insert_event(next_event, trigger_time=event.timespan, scope=scope_obj)
            else:
                new_temp = target

        # Update the temperature property if something changed
        if changed:
            self.greenhouse.set_property("temperature", new_temp)

    def on_moisture_event(self, event: Event) -> None:
        """Moisture handler mirroring `on_temperature_event` but constrained to [0.0, 1.0].

        Supports event-driven keys: `set`, `alter`, `relative_alter`, `gradual_change`.
        - `set` / `alter`: additive deltas applied to current value
        - `relative_alter`: multiplicative relative change
        - `gradual_change`: move 25% toward target and reschedule if not close
        """
        # Require an anchored system for moisture events. If none is provided
        # log an error and ignore the event (don't fall back to `self.greenhouse`).
        if getattr(event, "system", None) is None:
            _logger.error("moisture event received with no anchored system; ignoring event: %r", event)
            return

        target_system = event.system
        if target_system is None:
            return

        current = target_system.get_property("moisture", None)
        if current is None:
            return

        # Only modify moisture when the event explicitly specifies an action
        changed = False
        new_m = None

        # Case 1: event-specified absolute set
        if (event.get_property("set") is not None):
            new_m = event.get_property("set")
            changed = True

        # Case 2: event-specified additive alter
        elif (event.get_property("alter") is not None):
            new_m = event.get_property("alter") + current
            changed = True

        # Case 3: event-specified relative alter (percentage)
        elif (event.get_property("relative_alter") is not None):
            new_m = (1 + event.get_property("relative_alter")) * current
            changed = True

        # Case 4: gradual change toward a target
        elif (event.get_property("gradual_change") is not None):
            target = event.get_property("gradual_change")
            new_m = current + (target - current) * 0.25
            changed = True

            # Trigger the next event if the delta is larger than a small threshold
            if abs(new_m - target) > 0.01:
                next_event = Event(data=event.data.copy(), timespan=event.timespan)
                scope_obj = self.domain.get_scope("environment/moisture") if self.domain else None
                self.scheduler.insert_event(next_event, trigger_time=event.timespan, scope=scope_obj)
            else:
                new_m = target

        # Clamp to valid moisture range [0, 1] and update only if changed
        if changed:
            new_m = max(0.0, min(1.0, new_m))
            target_system.set_property("moisture", new_m)

    def on_light_event(self, event: Event) -> None:
        # Require an anchored system for light events. If none is provided
        # log an error and ignore the event (don't fall back to `self.greenhouse`).
        if getattr(event, "system", None) is None:
            _logger.error("light event received with no anchored system; ignoring event: %r", event)
            return

        target_system = event.system
        if target_system is None:
            return

        current = target_system.get_property("light", None)
        if current is None:
            return

        changed = False
        new_l = None

        # Support optional keys similar to temperature/moisture
        if (event.get_property("set") is not None):
            new_l = event.get_property("set")
            changed = True
        elif (event.get_property("alter") is not None):
            new_l = event.get_property("alter") + current
            changed = True
        elif (event.get_property("relative_alter") is not None):
            new_l = (1 + event.get_property("relative_alter")) * current
            changed = True

        if changed:
            target_system.set_property("light", new_l)

    def handle_heat_loss(self, system: Optional[SystemInstance], process: Optional[Process], duration: datetime.timedelta) -> None:
        """Handle the HeatLoss process for a given system over a duration.

        This is a stub method; no business logic is implemented here.
        Integrate with `Process` and `Store` structures as needed to model
        heat transfer, energy consumption, and resulting temperature changes.

        Args:
            system: The anchored system instance that experiences heat loss.
            process: The `Process` definition representing the HeatLoss behavior.
            duration: The time span over which to apply the HeatLoss process.
        """
        # Intentionally left unimplemented.
        pass

    # --- convenience run loop ---
    def run_and_dispatch(self, until: Optional[datetime.datetime] = None) -> None:
        """Run the scheduler and dispatch events to handlers until the queue drains (or until time)."""
        if until is None:
            # Use the scheduler's run helper but dispatch each event as it occurs
            while True:
                ev = self.scheduler.step()
                if ev is None:
                    break
                self.dispatch_event(ev)
        else:
            # Run up to until: step until the next event would be after `until`
            while self.scheduler.peek_events():
                next_time = self.scheduler.peek_events()[0][0]
                next_time = self.scheduler.peek_events()[0][0]
                if next_time > until:
                    break
                ev = self.scheduler.step()
                if ev is None:
                    break
                self.dispatch_event(ev)
            if self.scheduler.now < until:
                self.scheduler.now = until


__all__ = ["GreenhouseSimulation"]
