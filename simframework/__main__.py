"""Demo: instantiate scheduler, populate with events from a domain YAML, and process."""
import datetime
from pathlib import Path

try:
    # Prefer absolute import when run as a module
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.scope import Domain, Scope
    from simframework.engine import SimulationEngine
    from simframework.entity import Entity
except ImportError:
    # Fallback for running in environments where absolute imports fail
    from .scheduler import Scheduler
    from .event import Event
    from .scope import Domain, Scope
    from .engine import SimulationEngine
    from .entity import Entity


def main():
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    engine = SimulationEngine(start_time=start_time)
    scheduler = engine.scheduler

    # Attempt to load a domain definition for the simulation (GreenHouse)
    pkg_root = Path(__file__).resolve().parents[1]
    domain_yaml = pkg_root / "simulations" / "GreenHouse" / "domain.yaml"
    if domain_yaml.exists():
        domain = Domain.from_yaml(str(domain_yaml))
        top_scopes = domain.scopes_at_depth(0)
    else:
        domain = None

    # Instantiate a Greenhouse system if available
    greenhouse = None
    if domain is not None:
        gh_tmpl = domain.get_system_template("Greenhouse")
        if gh_tmpl is not None:
            greenhouse = gh_tmpl.instantiate(instance_id="greenhouse-1")
            engine.add_system_instance(greenhouse)

    if greenhouse is not None:
        print(f"INSTANCED: {greenhouse.id} (template={greenhouse.template.name})")
        print(f"Properties: {greenhouse.resolved_properties}")

    # Schedule a few environment-related events (temperature, moisture, light)
    dom_scopes = {}
    if domain is not None:
        dom_scopes["environment/temperature"] = domain.get_scope("environment/temperature")
        dom_scopes["environment/moisture"] = domain.get_scope("environment/moisture")
        dom_scopes["environment/light"] = domain.get_scope("environment/light")

    event_defs = [
        (30.0, "environment/temperature", datetime.timedelta(minutes=10)),
        (60.0, "environment/moisture", datetime.timedelta(minutes=5)),
        (90.0, "environment/light", datetime.timedelta(minutes=15)),
    ]

    total_events = 0
    for idx, (trigger_seconds, scope_path, timespan) in enumerate(event_defs, start=1):
        event = Event(data={"event_id": idx, "type": scope_path}, timespan=timespan)
        scope_obj = dom_scopes.get(scope_path)
        scheduler.insert_event(event, trigger_time=trigger_seconds, scope=scope_obj)
        total_events += 1

    print(f"Starting simulation at {scheduler.now}")
    print(f"Total events scheduled: {total_events}")
    print("=" * 90)

    # Phase 1: Peek ahead at environment events (without removing them)
    print("PHASE 1: Upcoming 'environment' events (preview)")
    print("-" * 90)

    env_scope = domain.get_scope("environment") if domain is not None else None
    environment_events = scheduler.peek_events(scope=env_scope) if env_scope is not None else []
    for _, (run_at, event) in enumerate(environment_events, start=1):
        scope_name = event.scope.name if getattr(event, "scope", None) is not None else "-"
        event_id = event.data.get("event_id", "-")
        print(
            f"ID: {event_id} | Time: {run_at.strftime('%Y-%m-%d %H:%M:%S')} | Scope: {scope_name} | Timespan: {event.timespan}")

    print(f"\nPhase 1 complete: {len(environment_events)} 'environment' events found in queue (not removed)")
    print("=" * 90)

    # Phase 2: Process all events normally (in chronological order)
    print("\nPHASE 2: Processing all events chronologically")
    print("-" * 90)
    event_num = 0
    while True:
        event = scheduler.step()
        if event is None:
            break
        scope_name = event.scope.name if getattr(event, "scope", None) is not None else "-"
        event_id = event.data.get("event_id", "-")
        print(
            f"ID: {event_id} | Time: {scheduler.now.strftime('%Y-%m-%d %H:%M:%S')} | Scope: {scope_name} | Timespan: {event.timespan}")

    print("=" * 90)
    print(f"Simulation ended at {scheduler.now}")
    print(f"Total elapsed time: {(scheduler.now - start_time).total_seconds() / 60:.1f} minutes")


if __name__ == "__main__":
    main()
