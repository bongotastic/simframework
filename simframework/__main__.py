"""Demo: instantiate scheduler, populate with events from a domain YAML, and process."""
import datetime
from pathlib import Path

try:
    # Prefer absolute import when run as a module
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.scope import Domain, Scope
except ImportError:
    # Fallback for running in environments where absolute imports fail
    from .scheduler import Scheduler
    from .event import Event
    from .scope import Domain, Scope


def main():
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    scheduler = Scheduler(start_time=start_time)

    # Attempt to load a domain definition for the simulation (LunarStation)
    pkg_root = Path(__file__).resolve().parents[1]
    domain_yaml = pkg_root / "simulations" / "LunarStation" / "domain.yaml"
    if domain_yaml.exists():
        domain = Domain.from_yaml(str(domain_yaml))
        top_scopes = domain.scopes_at_depth(0)
        categories = top_scopes if top_scopes else [Scope("weather"), Scope("communication"), Scope("personnel")]
    else:
        domain = None
        categories = [Scope("weather"), Scope("communication"), Scope("personnel")]

    # Generate 40 events spread across 1-120 minutes in the future
    five_min_delta = datetime.timedelta(minutes=5)

    for i in range(1, 41):
        # Spread events across 1-120 minutes (i * 3 minutes each)
        trigger_minute = i * 3
        assigned_scope = categories[i % len(categories)]

        # Every 5th event has a fixed 5-minute timespan; others vary
        if i % 5 == 0:
            timespan = five_min_delta
        else:
            timespan = datetime.timedelta(minutes=i % 20 + 1)

        event = Event(
            data={
                "event_id": i,
                "trigger_minute": trigger_minute,
            },
            timespan=timespan,
        )

        # Attach the scope object from the domain when available
        if domain is not None:
            scope_obj = assigned_scope
        else:
            # assigned_scope may be a plain Scope objects in the no-domain case
            scope_obj = assigned_scope

        scheduler.insert_event(
            event,
            trigger_time=trigger_minute * 60,  # Convert minutes to seconds
            scope=scope_obj,
        )

    print(f"Starting simulation at {scheduler.now}")
    print(f"Total events scheduled: 40 (spread across 1-120 minutes)")
    print("=" * 90)

    # Phase 1: Peek ahead at personnel events (without removing them)
    print("PHASE 1: Upcoming 'personnel' events (preview)")
    print("-" * 90)

    # If domain uses different naming, select personnel/people mapping
    people_label = "people"
    if domain is not None and domain.get_scope("personnel") is not None:
        people_label = "personnel"

    personnel_events = scheduler.peek_events(scope=domain.get_scope(people_label) if domain is not None else None)
    for event_num, (run_at, event) in enumerate(personnel_events, start=1):
        elapsed_minutes = (run_at - start_time).total_seconds() / 60
        scope_path = event.scope.full_path() if getattr(event, "scope", None) is not None else "-"
        print(
            f"Event #{event_num:2d} | Timestamp: {run_at} | Elapsed: {elapsed_minutes:6.1f} min | "
            f"Scope: {event.scope.name if getattr(event, 'scope', None) is not None else '-':12s} | ScopePath: {scope_path:30s} | Timespan: {event.timespan} | "
            f"ID: {event.data['event_id']}")

    print(f"\nPhase 1 complete: {len(personnel_events)} '{people_label}' events found in queue (not removed)")
    print("=" * 90)

    # Phase 2: Process all events normally (in chronological order)
    print("\nPHASE 2: Processing all events chronologically")
    print("-" * 90)
    event_num = 0
    while True:
        event = scheduler.step()
        if event is None:
            break
        event_num += 1
        elapsed_minutes = (scheduler.now - start_time).total_seconds() / 60
        scope_path = event.scope.full_path() if getattr(event, "scope", None) is not None else "-"
        print(
            f"Event #{event_num:2d} | Timestamp: {scheduler.now} | Elapsed: {elapsed_minutes:6.1f} min | "
            f"Scope: {event.scope.name if getattr(event, 'scope', None) is not None else '-':12s} | ScopePath: {scope_path:30s} | Timespan: {event.timespan} | "
            f"ID: {event.data['event_id']}")

    print("=" * 90)
    print(f"Simulation ended at {scheduler.now}")
    print(f"Total elapsed time: {(scheduler.now - start_time).total_seconds() / 60:.1f} minutes")


if __name__ == "__main__":
    main()
