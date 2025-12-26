import datetime
from datetime import timedelta
import pytest

try:
    from simframework.system import SystemTemplate
    from simframework.scheduler import Scheduler
    from simframework.event import Event
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.system import SystemTemplate
    from simframework.scheduler import Scheduler
    from simframework.event import Event


class TestSystemModel:
    def test_template_instantiate_and_equality(self):
        tmpl = SystemTemplate("population", properties={"size": 100})
        a = tmpl.instantiate(instance_id="pop-A", members=100)
        b = tmpl.instantiate(instance_id="pop-B", members=50)
        assert a != b
        assert hash(a) != hash(b)


class TestSchedulerSystemFiltering:
    def test_pop_event_for_system(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        tmpl = SystemTemplate("node")
        n1 = tmpl.instantiate(instance_id="n1")
        n2 = tmpl.instantiate(instance_id="n2")

        e1 = Event(data={"id": "n1-1"})
        e2 = Event(data={"id": "n2-1"})
        e3 = Event(data={"id": "n1-2"})

        s.insert_event(e1, trigger_time=5.0, system=n1)
        s.insert_event(e2, trigger_time=3.0, system=n2)
        s.insert_event(e3, trigger_time=10.0, system=n1)

        popped_n1 = s.pop_event_for_system(n1)
        assert popped_n1.data["id"] == "n1-1"

        popped_n2 = s.pop_event_for_system(n2)
        assert popped_n2.data["id"] == "n2-1"

        # Next n1 event should still be available
        popped_n1_again = s.pop_event_for_system(n1)
        assert popped_n1_again.data["id"] == "n1-2"

    def test_pop_event_for_system_not_found(self):
        s = Scheduler()
        tmpl = SystemTemplate("unit")
        inst = tmpl.instantiate(instance_id="u1")
        popped = s.pop_event_for_system(inst)
        assert popped is None
