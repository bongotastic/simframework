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

    def test_transitive_and_inherent_properties(self):
        # owner is transitive (propagates), serial is inherent (local only)
        parent_tmpl = SystemTemplate(
            "machine",
            properties={
                "owner": {"default": "Factory", "transitive": True},
                "serial": {"default": "PARENT-SN", "transitive": False},
            },
        )
        child_tmpl = SystemTemplate("subassembly", properties={"serial": "CHILD-SN"})
        parent_tmpl.add_child(child_tmpl)

        parent_inst = parent_tmpl.instantiate(instance_id="m1")
        assert len(parent_inst.children) == 1
        child_inst = parent_inst.children[0]

        # Transitive property bubbles down
        assert child_inst.get_property("owner") == "Factory"
        # Inherent property does not bubble down
        assert child_inst.get_property("serial") == "CHILD-SN"
        # Override transitive on child
        child_inst.set_property("owner", "Line-7")
        assert child_inst.get_property("owner") == "Line-7"
        # Resolved properties merge defaults and overrides
        assert child_inst.resolved_properties["owner"] == "Line-7"
        assert child_inst.resolved_properties["serial"] == "CHILD-SN"
        # Parent retains its value
        assert parent_inst.get_property("owner") == "Factory"


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

    def test_descendant_filtering(self):
        s = Scheduler()
        root_tmpl = SystemTemplate("org", properties={"owner": {"default": "HQ", "transitive": True}})
        child_tmpl = SystemTemplate("team")
        root_tmpl.add_child(child_tmpl)
        root = root_tmpl.instantiate(instance_id="root")
        child = root.children[0]

        e_root = Event(data={"id": "root-1"})
        e_child = Event(data={"id": "child-1"})

        s.insert_event(e_root, trigger_time=1.0, system=root)
        s.insert_event(e_child, trigger_time=2.0, system=child)

        # Peek with descendant matching should return both, ordered by time
        peeked = s.peek_events(system=root, include_descendants=True)
        assert [ev.data["id"] for _, ev in peeked] == ["root-1", "child-1"]

        # Pop only root
        popped_root = s.pop_event_for_system(root)
        assert popped_root.data["id"] == "root-1"

        # Pop including descendants returns the child
        popped_child = s.pop_event_for_system(root, include_descendants=True)
        assert popped_child.data["id"] == "child-1"
