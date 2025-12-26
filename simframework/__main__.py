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

    # Instantiate a StationTypeA and two astronaut agents (if templates are available)
    station_instance = None
    astronaut_instances = []
    if domain is not None:
        st_template = domain.get_system_template("StationTypeA")
        if st_template is not None:
            station_instance = st_template.instantiate(instance_id="station-1")
            engine.add_system_instance(station_instance)

        ag_template = domain.get_agent_template("astronaut")
        if ag_template is not None:
            a1 = ag_template.instantiate(instance_id="astro-1")
            a2 = ag_template.instantiate(instance_id="astro-2")
            engine.add_agent(a1)
            engine.add_agent(a2)
            astronaut_instances = [a1, a2]

    # Print a brief instance summary
    print("\nINSTANCES:")
    if station_instance is not None:
        print(f"  Station: {station_instance.id} (template={station_instance.template.name})")
        if station_instance.children:
            child_names = ', '.join([c.template.name for c in station_instance.children])
            print(f"    Modules: {child_names}")
    if astronaut_instances:
        print(f"  Agents: {', '.join([a.id for a in astronaut_instances])}")

    # --- Demo setup: place modules/systems and entities, set agent locations and schedule interactions ---
    if station_instance is not None:
        # Register child modules as systems in the engine for lookup
        modules_by_name = {}
        for child in station_instance.children:
            engine.add_system_instance(child)
            modules_by_name[child.template.name] = child

        # Create sample entities located in different modules
        toolbox = Entity("toolbox")
        experiment = Entity("experiment")
        # Assign locations (simple attribute) to entities
        if "living_habitat" in modules_by_name:
            toolbox.location = modules_by_name["living_habitat"]
        if "science" in modules_by_name:
            experiment.location = modules_by_name["science"]
        engine.add_entity(toolbox, "toolbox-1")
        engine.add_entity(experiment, "experiment-1")

        # Place agents in different modules so their perceptions differ
        if astronaut_instances:
            a1, a2 = astronaut_instances
            if "living_habitat" in modules_by_name:
                a1.set_location(modules_by_name["living_habitat"])
            if "science" in modules_by_name:
                a2.set_location(modules_by_name["science"])

            # Show initial perception (location-based by default)
            for a in astronaut_instances:
                seen = a.perceive_entities(engine)
                seen_names = ", ".join([e.name for e in seen]) if seen else "(none)"
                print(f"Agent {a.id} at {a.location.id if a.location is not None else '-'} sees: {seen_names}")

            # Schedule an interaction: astronaut1 will interact with life_support in 60s
            if "life_support" in modules_by_name:
                life = modules_by_name["life_support"]
                a1.interact_with_system(engine, life.id, 60.0, lambda a_id=a1.id, sys_id=life.id: print(f"[Interaction] Agent {a_id} services {sys_id} at {scheduler.now}"))

            # Schedule a movement: astronaut2 moves to living_habitat in 120s
            if "living_habitat" in modules_by_name:
                dest = modules_by_name["living_habitat"]
                def move_agent(agent, to):
                    agent.set_location(to)
                    print(f"[Move] Agent {agent.id} moved to {to.id} at {scheduler.now}")
                scheduler.schedule(120.0, move_agent, a2, dest)

    # --- End demo setup ---

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
    for _, (run_at, event) in enumerate(personnel_events, start=1):
        scope_name = event.scope.name if getattr(event, "scope", None) is not None else "-"
        event_id = event.data.get("event_id", "-")
        print(
            f"ID: {event_id} | Time: {run_at.strftime('%Y-%m-%d %H:%M:%S')} | Scope: {scope_name} | Timespan: {event.timespan}")

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
        scope_name = event.scope.name if getattr(event, "scope", None) is not None else "-"
        event_id = event.data.get("event_id", "-")
        print(
            f"ID: {event_id} | Time: {scheduler.now.strftime('%Y-%m-%d %H:%M:%S')} | Scope: {scope_name} | Timespan: {event.timespan}")

    print("=" * 90)
    print(f"Simulation ended at {scheduler.now}")
    print(f"Total elapsed time: {(scheduler.now - start_time).total_seconds() / 60:.1f} minutes")


if __name__ == "__main__":
    main()
