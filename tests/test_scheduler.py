import datetime
from datetime import timedelta
import pytest

try:
    from simframework.scheduler import Scheduler
    from simframework.event import Event
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scheduler import Scheduler
    from simframework.event import Event


class TestSchedulerBasics:
    """Test basic scheduler initialization and properties."""

    def test_init_default_start_time(self):
        """Scheduler should initialize with current time if not provided."""
        s = Scheduler()
        assert isinstance(s.now, datetime.datetime)

    def test_init_custom_start_time(self):
        """Scheduler should accept a custom start time."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        assert s.now == start

    def test_init_invalid_start_time(self):
        """Scheduler should reject non-datetime start times."""
        with pytest.raises(TypeError):
            Scheduler(start_time=123.45)

    def test_now_property_getter(self):
        """now property should return current simulation time."""
        start = datetime.datetime(2025, 1, 1, 12, 0, 0)
        s = Scheduler(start_time=start)
        assert s.now == start

    def test_now_property_setter(self):
        """now property should allow setting simulation time."""
        s = Scheduler(start_time=datetime.datetime(2025, 1, 1, 0, 0, 0))
        new_time = datetime.datetime(2025, 1, 2, 0, 0, 0)
        s.now = new_time
        assert s.now == new_time

    def test_now_setter_invalid_type(self):
        """now setter should reject non-datetime values."""
        s = Scheduler()
        with pytest.raises(TypeError):
            s.now = "2025-01-01"


class TestScheduleMethod:
    """Test the schedule method with various delay formats."""

    def test_schedule_with_float_delay(self):
        """schedule should accept float delay (seconds)."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        run_at, idx = s.schedule(5.0)
        assert run_at == start + timedelta(seconds=5.0)
        assert idx == 0

    def test_schedule_with_timedelta_delay(self):
        """schedule should accept timedelta delay."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        delay = timedelta(hours=2)
        run_at, idx = s.schedule(delay)
        assert run_at == start + delay
        assert idx == 0

    def test_schedule_with_absolute_datetime(self):
        """schedule should accept absolute datetime independent of now."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        absolute_time = datetime.datetime(2025, 2, 1, 12, 30, 0)
        run_at, idx = s.schedule(absolute_time)
        assert run_at == absolute_time
        assert idx == 0

    def test_schedule_negative_delay_float(self):
        """schedule should reject negative float delay."""
        s = Scheduler()
        with pytest.raises(ValueError):
            s.schedule(-1.0)

    def test_schedule_negative_delay_timedelta(self):
        """schedule should reject negative timedelta delay."""
        s = Scheduler()
        with pytest.raises(ValueError):
            s.schedule(timedelta(seconds=-5))

    def test_schedule_invalid_delay_type(self):
        """schedule should reject invalid delay types."""
        s = Scheduler()
        with pytest.raises(TypeError):
            s.schedule("5 seconds")

    def test_schedule_increments_counter(self):
        """schedule should increment event counter for unique IDs."""
        s = Scheduler()
        _, idx1 = s.schedule(1.0)
        _, idx2 = s.schedule(2.0)
        _, idx3 = s.schedule(3.0)
        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2

    def test_schedule_with_custom_event(self):
        """schedule should accept pre-built Event objects."""
        s = Scheduler()
        event = Event(data={"custom": "data"}, timespan=timedelta(hours=1))
        run_at, idx = s.schedule(5.0, event=event)
        assert run_at is not None
        assert idx == 0


class TestInsertEventMethod:
    """Test the insert_event method."""

    def test_insert_event_basic(self):
        """insert_event should add event to queue."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        event = Event(data={"test": 1})
        run_at, idx = s.insert_event(event, trigger_time=10.0)
        assert run_at == start + timedelta(seconds=10.0)
        assert event.scope is None
        assert idx == 0

    def test_insert_event_absolute_datetime(self):
        """insert_event should handle absolute datetime trigger_time."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        absolute_time = datetime.datetime(2025, 1, 5, 10, 0, 0)
        event = Event(data={"test": 2})
        run_at, idx = s.insert_event(event, trigger_time=absolute_time)
        assert run_at == absolute_time

    def test_insert_event_timedelta(self):
        """insert_event should handle timedelta trigger_time."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        delay = timedelta(days=3, hours=5)
        event = Event(data={"test": 3})
        run_at, idx = s.insert_event(event, trigger_time=delay)
        assert run_at == start + delay

    def test_insert_event_with_scope(self):
        """insert_event should attach a Scope to the event when provided."""
        s = Scheduler()
        from simframework.scope import Scope
        event = Event(data={"test": 4})
        scope = Scope("growth")
        s.insert_event(event, trigger_time=5.0, scope=scope)
        assert event.scope == scope

    def test_insert_event_invalid_event_type(self):
        """insert_event should reject non-Event objects."""
        s = Scheduler()
        with pytest.raises(TypeError):
            s.insert_event({"data": "dict"}, trigger_time=5.0)

    def test_insert_event_invalid_trigger_time(self):
        """insert_event should reject invalid trigger_time types."""
        s = Scheduler()
        event = Event(data={"test": 5})
        with pytest.raises(TypeError):
            s.insert_event(event, trigger_time="tomorrow")

    def test_insert_event_negative_seconds(self):
        """insert_event should reject negative trigger_time (seconds)."""
        s = Scheduler()
        event = Event(data={"test": 6})
        with pytest.raises(ValueError):
            s.insert_event(event, trigger_time=-5.0)


class TestPopEventMethod:
    """Test the pop_event method."""

    def test_pop_event_empty_queue(self):
        """pop_event should return None on empty queue."""
        s = Scheduler()
        result = s.pop_event()
        assert result is None

    def test_pop_event_no_scope_filter(self):
        """pop_event with no scope should return earliest event."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        s.insert_event(event3, trigger_time=3.0)
        s.insert_event(event1, trigger_time=1.0)
        s.insert_event(event2, trigger_time=2.0)
        popped = s.pop_event()
        assert popped.data["id"] == 1

    def test_pop_event_with_scope_filter(self):
        """pop_event with scope should return earliest event in that scope."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        from simframework.scope import Scope
        scope_weather = Scope("weather")
        scope_growth = Scope("growth")
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        s.insert_event(event1, trigger_time=1.0, scope=scope_weather)
        s.insert_event(event2, trigger_time=2.0, scope=scope_growth)
        s.insert_event(event3, trigger_time=3.0, scope=scope_weather)
        popped = s.pop_event(scope=scope_weather)
        assert popped.data["id"] == 1

    def test_pop_event_scope_not_found(self):
        """pop_event with non-matching scope should return None."""
        s = Scheduler()
        from simframework.scope import Scope
        event = Event(data={"id": 1})
        s.insert_event(event, trigger_time=1.0, scope=Scope("weather"))
        popped = s.pop_event(scope=Scope("nonexistent"))
        assert popped is None

    def test_pop_event_removes_from_queue(self):
        """pop_event should remove event from queue."""
        s = Scheduler()
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        s.insert_event(event1, trigger_time=1.0)
        s.insert_event(event2, trigger_time=2.0)
        popped = s.pop_event()
        assert popped.data["id"] == 1
        # Next pop should get event2
        popped = s.pop_event()
        assert popped.data["id"] == 2
        # Queue should be empty
        popped = s.pop_event()
        assert popped is None

    def test_pop_event_maintains_heap_order(self):
        """pop_event should maintain chronological order after partial removal."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        from simframework.scope import Scope
        cat1 = Scope("cat1")
        cat2 = Scope("cat2")
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        event4 = Event(data={"id": 4})
        s.insert_event(event1, trigger_time=1.0, scope=cat1)
        s.insert_event(event2, trigger_time=2.0, scope=cat2)
        s.insert_event(event3, trigger_time=3.0, scope=cat1)
        s.insert_event(event4, trigger_time=4.0, scope=cat2)
        # Pop cat1 events, leaving cat2 intact
        popped = s.pop_event(scope=cat1)
        assert popped.data["id"] == 1
        # cat2 events should still be in order
        popped = s.pop_event(scope=cat2)
        assert popped.data["id"] == 2
        popped = s.pop_event(scope=cat2)
        assert popped.data["id"] == 4


class TestStepAndRunMethods:
    """Test step and run methods."""

    def test_step_empty_queue(self):
        """step on empty queue should return None."""
        s = Scheduler()
        result = s.step()
        assert result is None

    def test_step_advances_time(self):
        """step should advance now to event's trigger time."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(5.0)
        s.step()
        assert s.now == start + timedelta(seconds=5.0)

    def test_step_returns_event(self):
        """step should return the Event object."""
        s = Scheduler()
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0)
        result = s.step()
        assert result == e
        assert result.data["id"] == 1

    def test_step_multiple_calls(self):
        """Multiple step calls should process events in order."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(1.0)
        s.schedule(2.0)
        s.schedule(3.0)
        
        s.step()
        assert s.now == start + timedelta(seconds=1.0)
        
        s.step()
        assert s.now == start + timedelta(seconds=2.0)
        
        s.step()
        assert s.now == start + timedelta(seconds=3.0)

    def test_run_empty_queue(self):
        """run on empty queue should not error."""
        s = Scheduler()
        s.run()  # Should complete without error

    def test_run_processes_all_events(self):
        """run should process all scheduled events."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(1.0)
        s.schedule(2.0)
        s.schedule(3.0)
        s.run()
        assert s.now == start + timedelta(seconds=3.0)
        assert s.pop_event() is None

    def test_run_with_until_time(self):
        """run(until=T) should stop processing events after time T."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(1.0)
        s.schedule(2.0)
        s.schedule(3.0)
        until_time = start + timedelta(seconds=2.5)
        s.run(until=until_time)
        assert s.now == until_time
        
        # Verify next event is still there
        next_event = s.pop_event()
        assert next_event is not None

    def test_run_advances_time_to_until(self):
        """run(until=T) should advance now to T even if no events fire after."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(1.0)
        until_time = start + timedelta(seconds=5.0)
        s.run(until=until_time)
        assert s.now == until_time


class TestEventOrdering:
    """Test that events maintain proper chronological ordering."""

    def test_events_processed_in_chronological_order(self):
        """Events should be processed in chronological order regardless of insertion order."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        
        # Insert events out of order
        s.schedule(5.0)
        s.schedule(1.0)
        s.schedule(3.0)
        s.schedule(2.0)

        s.step()
        assert s.now == start + timedelta(seconds=1.0)
        s.step()
        assert s.now == start + timedelta(seconds=2.0)
        s.step()
        assert s.now == start + timedelta(seconds=3.0)
        s.step()
        assert s.now == start + timedelta(seconds=5.0)

    def test_events_with_same_time_use_insertion_order(self):
        """Events with same trigger time should use insertion order (idx tie-breaker)."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        
        s.schedule(1.0, event=Event(data={"id": "a"}))
        s.schedule(1.0, event=Event(data={"id": "b"}))
        s.schedule(1.0, event=Event(data={"id": "c"}))

        e1 = s.step()
        e2 = s.step()
        e3 = s.step()

        assert e1.data["id"] == "a"
        assert e2.data["id"] == "b"
        assert e3.data["id"] == "c"


class TestEventTimespan:
    """Test event timespan handling."""

    def test_event_timespan_default(self):
        """Event should default to zero timespan."""
        event = Event(data={"test": 1})
        assert event.timespan == timedelta(0)

    def test_event_timespan_custom(self):
        """Event should store custom timespan."""
        span = timedelta(hours=2, minutes=30)
        event = Event(data={"test": 2}, timespan=span)
        assert event.timespan == span

    def test_insert_event_preserves_timespan(self):
        """insert_event should preserve event's timespan."""
        s = Scheduler()
        span = timedelta(minutes=45)
        event = Event(data={"test": 3}, timespan=span)
        s.insert_event(event, trigger_time=5.0)
        popped = s.pop_event()
        assert popped.timespan == span
