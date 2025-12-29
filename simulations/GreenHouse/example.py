"""Example script demonstrating the `GreenhouseSimulation` helper.

Run this script with:
    python simulations/GreenHouse/example.py

Or run it as a module from the project root:
    python -m simulations.GreenHouse.example

It sets up a greenhouse, schedules example environment events, and
runs the dispatch loop demonstrating property updates.
"""
from pathlib import Path
import datetime

try:
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event
except Exception:
    # Allow running when project root is not a package on sys.path
    import sys
    pkg_root = Path(__file__).resolve().parents[2]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event


def main():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"

    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-example")
    if gh is None:
        print("No Greenhouse defined in domain.yaml")
        return

    print("Initial properties:")
    print(gh.resolved_properties)

    # Gradual change in temperature
    # Add a special event to increase temperature to 30°C using gradual_change
    print("Scheduling a gradual temperature change to 30°C (target)")
    temp_target_event = Event(data={"gradual_change": 30.0, "type": "environment/temperature"}, timespan=datetime.timedelta(minutes=30), system=gh)
    
    # schedule to occur shortly after start (2 seconds)
    temp_scope = sim.domain.get_scope("environment/temperature") if sim.domain else None
    sim.scheduler.insert_event(temp_target_event, trigger_time=2.0, scope=temp_scope)

    # Increase by 10% of light level
    print("Scheduling a 10% increase in light level")
    light_increase_event = Event(data={"relative_alter": 0.1, "type": "environment/light"}, timespan=datetime.timedelta(minutes=15), system=gh)
    light_scope = sim.domain.get_scope("environment/light") if sim.domain else None
    sim.scheduler.insert_event(light_increase_event, trigger_time=60.0, scope=light_scope)

    sim.print_status()

    print("Running simulation and dispatching events...")
    sim.run_and_dispatch()

    sim.print_status()

    print("Final properties:")
    print(gh.resolved_properties)


if __name__ == "__main__":
    main()
