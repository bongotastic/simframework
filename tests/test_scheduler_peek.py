import datetime
from datetime import timedelta
import pytest

try:
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.system import SystemTemplate
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.system import SystemTemplate


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
        assert peeked[0].data["id"] == 1

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

    def test_peek_events_filter_by_category(self):
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        
        s.insert_event(e1, trigger_time=1.0, category="weather")
        s.insert_event(e2, trigger_time=2.0, category="growth")
        s.insert_event(e3, trigger_time=3.0, category="weather")
        
        weather_events = s.peek_events(category="weather")
        assert len(weather_events) == 2
        assert weather_events[0].data["id"] == 1
        assert weather_events[1].data["id"] == 3

    def test_peek_events_filter_by_system(self):
        s = Scheduler()
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
        assert sys_a_events[0].data["id"] == 1
        assert sys_a_events[1].data["id"] == 3

    def test_peek_events_with_limit(self):
        s = Scheduler()
        for i in range(1, 6):
            e = Event(data={"id": i})
            s.insert_event(e, trigger_time=float(i))
        
        peeked = s.peek_events(limit=3)
        assert len(peeked) == 3
        assert [ev.data["id"] for ev in peeked] == [1, 2, 3]

    def test_peek_events_combined_filters(self):
        s = Scheduler()
        tmpl = SystemTemplate("unit")
        sys_a = tmpl.instantiate(instance_id="a")
        
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        e4 = Event(data={"id": 4})
        
        s.insert_event(e1, trigger_time=1.0, category="weather", system=sys_a)
        s.insert_event(e2, trigger_time=2.0, category="growth", system=sys_a)
        s.insert_event(e3, trigger_time=3.0, category="weather", system=sys_a)
        s.insert_event(e4, trigger_time=4.0, category="weather")
        
        # Filter by category AND system
        filtered = s.peek_events(category="weather", system=sys_a)
        assert len(filtered) == 2
        assert filtered[0].data["id"] == 1
        assert filtered[1].data["id"] == 3

    def test_peek_events_no_match_returns_empty(self):
        s = Scheduler()
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0, category="weather")
        
        peeked = s.peek_events(category="nonexistent")
        assert peeked == []
