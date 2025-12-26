import datetime
from datetime import timedelta
import pytest

try:
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.system import SystemTemplate
    from simframework.scope import Scope
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.system import SystemTemplate
    from simframework.scope import Scope


class TestSchedulerPeek:
    def test_peek_events_empty_queue(self):
        s = Scheduler()
        events = s.peek_events()
        assert events == []

    def test_peek_events_returns_events_in_heap_order(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        
        # Insert in reverse order to test heap ordering
        s.insert_event(e3, trigger_time=3.0)
        s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        
        peeked = s.peek_events()
        assert len(peeked) == 3
        # Verify first event is the earliest (heap guarantees this)
        run_at, event = peeked[0]
        assert event.data["id"] == 1
        assert run_at == start + timedelta(seconds=1.0)

    def test_peek_events_does_not_modify_queue(self):
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        
        peeked1 = s.peek_events()
        peeked2 = s.peek_events()
        
        assert peeked1 == peeked2
        assert len(peeked1) == 2

    def test_peek_events_filter_by_scope(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        from simframework.scope import Scope
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        
        scope_weather = Scope("weather")
        scope_growth = Scope("growth")
        s.insert_event(e1, trigger_time=1.0, scope=scope_weather)
        s.insert_event(e2, trigger_time=2.0, scope=scope_growth)
        s.insert_event(e3, trigger_time=3.0, scope=scope_weather)
        
        weather_events = s.peek_events(scope=scope_weather)
        assert len(weather_events) == 2
        assert weather_events[0][1].data["id"] == 1
        assert weather_events[1][1].data["id"] == 3

    def test_peek_events_filter_by_system(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        tmpl = SystemTemplate("unit")
        sys_a = tmpl.instantiate(instance_id="a")
        sys_b = tmpl.instantiate(instance_id="b")
        
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        
        s.insert_event(e1, trigger_time=1.0, system=sys_a)
        s.insert_event(e2, trigger_time=2.0, system=sys_b)
        s.insert_event(e3, trigger_time=3.0, system=sys_a)
        
        sys_a_events = s.peek_events(system=sys_a)
        assert len(sys_a_events) == 2
        assert sys_a_events[0][1].data["id"] == 1
        assert sys_a_events[1][1].data["id"] == 3

    def test_peek_events_filter_by_system_descendants(self):
        s = Scheduler()
        parent_tmpl = SystemTemplate("org", properties={"owner": {"default": "HQ", "transitive": True}})
        child_tmpl = SystemTemplate("dept")
        parent_tmpl.add_child(child_tmpl)
        root = parent_tmpl.instantiate(instance_id="root")
        child = root.children[0]

        e_root = Event(data={"id": "root"})
        e_child = Event(data={"id": "child"})
        s.insert_event(e_root, trigger_time=1.0, system=root)
        s.insert_event(e_child, trigger_time=2.0, system=child)

        descendants = s.peek_events(system=root, include_descendants=True)
        assert [ev.data["id"] for _, ev in descendants] == ["root", "child"]

    def test_peek_events_with_limit(self):
        s = Scheduler()
        for i in range(1, 6):
            e = Event(data={"id": i})
            s.insert_event(e, trigger_time=float(i))
        
        peeked = s.peek_events(limit=3)
        assert len(peeked) == 3
        assert [ev[1].data["id"] for ev in peeked] == [1, 2, 3]

    def test_peek_events_combined_filters(self):
        s = Scheduler()
        tmpl = SystemTemplate("unit")
        sys_a = tmpl.instantiate(instance_id="a")
        
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        e4 = Event(data={"id": 4})
        
        from simframework.scope import Scope
        scope_weather = Scope("weather")
        scope_growth = Scope("growth")
        s.insert_event(e1, trigger_time=1.0, scope=scope_weather, system=sys_a)
        s.insert_event(e2, trigger_time=2.0, scope=scope_growth, system=sys_a)
        s.insert_event(e3, trigger_time=3.0, scope=scope_weather, system=sys_a)
        s.insert_event(e4, trigger_time=4.0, scope=scope_weather)
        
        # Filter by scope AND system
        filtered = s.peek_events(scope=scope_weather, system=sys_a)
        assert len(filtered) == 2
        assert filtered[0][1].data["id"] == 1
        assert filtered[1][1].data["id"] == 3

    def test_peek_events_no_match_returns_empty(self):
        s = Scheduler()
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0, scope=Scope("weather"))
        
        peeked = s.peek_events(scope=Scope("nonexistent"))
        assert peeked == []
