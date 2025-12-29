import datetime
from datetime import timedelta

try:
    from simframework.engine import SimulationEngine
    from simframework.system import SystemTemplate
    from simframework.event import Event
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.engine import SimulationEngine
    from simframework.system import SystemTemplate
    from simframework.event import Event


class TestSimulationEngine:
    def test_add_get_remove_system(self):
        eng = SimulationEngine()
        tmpl = SystemTemplate("node")
        n1 = tmpl.instantiate(instance_id="n1")
        sid = eng.add_system_instance(n1)
        assert sid == "n1"
        assert eng.get_system("n1") == n1
        rem = eng.remove_system("n1")
        assert rem == n1
        assert eng.get_system("n1") is None

    def test_schedule_for_system_attaches_system(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        eng = SimulationEngine(start_time=start)
        tmpl = SystemTemplate("node")
        n1 = tmpl.instantiate(instance_id="n1")
        eng.add_system_instance(n1)

        # Schedule an event for system n1
        eng.schedule_for_system("n1", 5.0)
        peeked = eng.scheduler.peek_events(system=n1)
        assert len(peeked) == 1
        run_at, ev = peeked[0]
        assert ev.system == n1
        assert run_at == start + timedelta(seconds=5.0)

    def test_agents_registry(self):
        eng = SimulationEngine()
        tmpl = SystemTemplate("unit")
        a = tmpl.instantiate(instance_id="a")
        aid = eng.add_agent(a)
        assert aid == "a"
        assert eng.get_agent("a") == a
        # agent also discoverable as system
        assert eng.get_system("a") == a
        rem = eng.remove_agent("a")
        assert rem == a
        assert eng.get_agent("a") is None
        assert eng.get_system("a") is None
