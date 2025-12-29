import datetime
from pathlib import Path
import sys
import pytest
import logging

try:
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event
except Exception:
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simulations.GreenHouse.simulation import GreenhouseSimulation
    from simframework.event import Event


def test_moisture_event_applies_to_anchored_system():
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "../simulations/GreenHouse/domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))

    gh1 = sim.setup_greenhouse(instance_id="gh1")
    gh2 = sim.setup_greenhouse(instance_id="gh2")
    assert gh1 is not None and gh2 is not None

    # Ensure gh1 and gh2 have default moisture
    assert gh1.get_property("moisture") == gh2.get_property("moisture")

    # Create an event anchored to gh1
    ev = Event(data={"alter": -0.05, "type": "environment/moisture"})
    ev.system = gh1

    # Apply event: should change gh1 but NOT gh2
    sim.on_moisture_event(ev)
    assert gh1.get_property("moisture") == pytest.approx(0.35 - 0.05)
    assert gh2.get_property("moisture") == pytest.approx(0.35)


def test_moisture_event_without_anchored_system_is_ignored(caplog):
    start = datetime.datetime(2025, 1, 1, 0, 0, 0)
    domain_yaml = Path(__file__).resolve().parent / "../simulations/GreenHouse/domain.yaml"
    sim = GreenhouseSimulation(start_time=start, domain_yaml=str(domain_yaml))

    gh = sim.setup_greenhouse(instance_id="gh-standalone")
    assert gh is not None

    ev = Event(data={"alter": -0.05, "type": "environment/moisture"})

    with caplog.at_level(logging.ERROR):
        sim.on_moisture_event(ev)

    # The greenhouse should be unchanged
    assert gh.get_property("moisture") == pytest.approx(0.35)

    # Verify an error was logged about missing anchored system
    assert any("no anchored system" in r.getMessage() for r in caplog.records)