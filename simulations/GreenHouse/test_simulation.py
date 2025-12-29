import datetime
from datetime import timedelta
import sys
from pathlib import Path
import pytest

try:
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event
except Exception:
    # Fallback when running tests from project root
    pkg_root = Path(__file__).resolve().parents[2]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event


def test_setup_greenhouse_and_properties():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))

    assert sim.domain is not None
    gh = sim.setup_greenhouse(instance_id="greenhouse-test")
    assert gh is not None

    # Check initial resolved properties from domain defaults
    props = gh.resolved_properties
    assert props.get("capacity") == 100
    assert props.get("temperature") == 22.0
    assert props.get("moisture") == 0.35
    assert props.get("light") == 12000


def test_schedule_and_dispatch_updates_properties():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-test-2")
    assert gh is not None

    scheduled = sim.schedule_environment_events()
    assert scheduled == 3

    # Ensure queued events include temperature / moisture / light types
    queued = sim.scheduler.peek_events()
    queued_types = [e.data.get("type") for _, e in queued]
    assert "environment/temperature" in queued_types
    assert "environment/moisture" in queued_types
    assert "environment/light" in queued_types

    # Step through events manually so we can inspect and dispatch each
    processed = []
    while True:
        ev = sim.scheduler.step()
        if ev is None:
            break
        processed.append((sim.scheduler.now, ev.data.get("type"), ev))
        sim.dispatch_event(ev)

    # Expect three events processed
    types_seen = [t for _, t, _ in processed]
    assert "environment/temperature" in types_seen
    assert "environment/moisture" in types_seen
    assert "environment/light" in types_seen

    # Directly invoke the moisture handler on the processed event to ensure handler logic works
    moisture_ev = next(ev for _, t, ev in processed if t == "environment/moisture")
    # Reset property and call handler directly
    gh.set_property("moisture", 0.35)

    # Debugging: validate event and current values
    print("DEBUG moisture_ev.data:", moisture_ev.data)
    print("DEBUG moisture_ev.timespan:", moisture_ev.timespan)
    print("DEBUG before_current:", gh.get_property("moisture"))
    assert gh.get_property("moisture") == 0.35

    sim.on_moisture_event(moisture_ev)
    print("DEBUG after_current:", gh.get_property("moisture"))

    # No default behavior: event without properties should not change moisture
    assert gh.get_property("moisture") == pytest.approx(0.35)

    # Sanity check: setting via set_property manually works
    gh.set_property("moisture", 0.34)
    assert gh.get_property("moisture") == pytest.approx(0.34)

    # Directly invoke the temperature handler for the processed temperature event; should NOT change since event has no properties
    temp_ev = next(ev for _, t, ev in processed if t == "environment/temperature")
    gh.set_property("temperature", 22.0)
    sim.on_temperature_event(temp_ev)
    assert gh.get_property("temperature") == pytest.approx(22.0)

    # After handlers: no default changes, light remains unchanged
    assert gh.get_property("light") == 12000

    # Queue should be empty now
    assert sim.scheduler.pop_event() is None


def test_run_and_dispatch_until_stops_early():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-test-3")
    assert gh is not None

    sim.schedule_environment_events()

    # Run until after second event but before third (65 seconds)
    until = start + timedelta(seconds=65)
    sim.run_and_dispatch(until=until)

    # Temperature and moisture should NOT have changed (no default behavior)
    import pytest
    assert gh.get_property("temperature") == pytest.approx(22.0)
    assert gh.get_property("moisture") == pytest.approx(0.35)
    # Light should still be unchanged (third event not processed)
    assert gh.get_property("light") == 12000

    # One event should remain in queue
    remaining = sim.scheduler.peek_events()
    assert len(remaining) == 1


def test_temperature_event_uses_event_properties_not_system():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-temp-event")
    assert gh is not None

    # Put conflicting property on the system (should be ignored in favor of event)
    gh.set_property("set", 100.0)
    gh.set_property("temperature", 22.0)

    ev = Event(data={"set": 5.0, "type": "environment/temperature"}, timespan=sim.scheduler.now - sim.scheduler.now)
    sim.dispatch_event(ev)

    # 'set' should set to the event value (absolute), so resulting temperature should be 5.0
    assert gh.get_property("temperature") == pytest.approx(5.0)

    # Alter should be additive: set current to 20 and alter by +2 -> expect 22
    gh.set_property("temperature", 20.0)
    ev2 = Event(data={"alter": 2.0, "type": "environment/temperature"})
    sim.dispatch_event(ev2)
    assert gh.get_property("temperature") == pytest.approx(22.0)

    # Relative alter: +10% of 20 -> 22; -10% -> 18
    gh.set_property("temperature", 20.0)
    ev3 = Event(data={"relative_alter": 0.1, "type": "environment/temperature"})
    sim.dispatch_event(ev3)
    assert gh.get_property("temperature") == pytest.approx(22.0)

    gh.set_property("temperature", 20.0)
    ev4 = Event(data={"relative_alter": -0.1, "type": "environment/temperature"})
    sim.dispatch_event(ev4)
    assert gh.get_property("temperature") == pytest.approx(18.0)


def test_moisture_event_uses_event_properties_not_system():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-moist-event")
    assert gh is not None

    # Conflicting system-level property
    gh.set_property("set", 1.0)
    gh.set_property("moisture", 0.5)

    ev = Event(data={"alter": -0.15, "type": "environment/moisture"})
    sim.dispatch_event(ev)

    # Alter is additive: 0.5 + (-0.15)
    assert gh.get_property("moisture") == pytest.approx(0.5 - 0.15)

    # Relative alter example: 0.5 with relative_alter=0.1 -> 0.55
    gh.set_property("moisture", 0.5)
    ev2 = Event(data={"relative_alter": 0.1, "type": "environment/moisture"})
    sim.dispatch_event(ev2)
    assert gh.get_property("moisture") == pytest.approx(0.5 * 1.1)


def test_gradual_change_schedules_followup_temperature_event():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-gradual-temp")
    assert gh is not None

    gh.set_property("temperature", 20.0)
    ev = Event(data={"gradual_change": 30.0, "type": "environment/temperature"}, timespan=datetime.timedelta(seconds=10))
    sim.dispatch_event(ev)

    # Because the delta is large, a follow-up event should be scheduled
    queued = sim.scheduler.peek_events()
    assert any(e.data.get("type") == "environment/temperature" for _, e in queued)

    # After dispatch, temperature should have moved 25% toward 30: 20 + (30-20)*0.25 = 22.5
    assert gh.get_property("temperature") == pytest.approx(22.5)


def test_gradual_change_schedules_followup_moisture_event():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-gradual-moist")
    assert gh is not None

    gh.set_property("moisture", 0.2)
    ev = Event(data={"gradual_change": 0.9, "type": "environment/moisture"}, timespan=datetime.timedelta(seconds=5))
    sim.dispatch_event(ev)

    queued = sim.scheduler.peek_events()
    assert any(e.data.get("type") == "environment/moisture" for _, e in queued)

    # After dispatch, moisture should have moved 25% toward 0.9: 0.2 + (0.9-0.2)*0.25 = 0.375
    assert gh.get_property("moisture") == pytest.approx(0.2 + (0.9 - 0.2) * 0.25)


def test_temperature_no_change_without_properties():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))
    gh = sim.setup_greenhouse(instance_id="greenhouse-temp-default")
    assert gh is not None

    gh.set_property("temperature", 22.0)
    ev = Event(data={"type": "environment/temperature"})
    sim.on_temperature_event(ev)
    assert gh.get_property("temperature") == pytest.approx(22.0)
