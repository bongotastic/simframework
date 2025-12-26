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
        run_at, idx = s.schedule(5.0, lambda: None)
        assert run_at == start + timedelta(seconds=5.0)
        assert idx == 0

    def test_schedule_with_timedelta_delay(self):
        """schedule should accept timedelta delay."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        delay = timedelta(hours=2)
        run_at, idx = s.schedule(delay, lambda: None)
        assert run_at == start + delay
        assert idx == 0

    def test_schedule_with_absolute_datetime(self):
        """schedule should accept absolute datetime independent of now."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        absolute_time = datetime.datetime(2025, 2, 1, 12, 30, 0)
        run_at, idx = s.schedule(absolute_time, lambda: None)
        assert run_at == absolute_time
        assert idx == 0

    def test_schedule_negative_delay_float(self):
        """schedule should reject negative float delay."""
        s = Scheduler()
        with pytest.raises(ValueError):
            s.schedule(-1.0, lambda: None)

    def test_schedule_negative_delay_timedelta(self):
        """schedule should reject negative timedelta delay."""
        s = Scheduler()
        with pytest.raises(ValueError):
            s.schedule(timedelta(seconds=-5), lambda: None)

    def test_schedule_invalid_delay_type(self):
        """schedule should reject invalid delay types."""
        s = Scheduler()
        with pytest.raises(TypeError):
            s.schedule("5 seconds", lambda: None)

    def test_schedule_increments_counter(self):
        """schedule should increment event counter for unique IDs."""
        s = Scheduler()
        _, idx1 = s.schedule(1.0, lambda: None)
        _, idx2 = s.schedule(2.0, lambda: None)
        _, idx3 = s.schedule(3.0, lambda: None)
        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2

    def test_schedule_with_custom_event(self):
        """schedule should accept pre-built Event objects."""
        s = Scheduler()
        event = Event(data={"custom": "data"}, timespan=timedelta(hours=1))
        run_at, idx = s.schedule(5.0, lambda: None, event=event)
        assert run_at is not None
        assert idx == 0


class TestInsertEventMethod:
    """Test the insert_event method."""

    def test_insert_event_basic(self):
        """insert_event should add event to queue."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        event = Event(data={"test": 1})
        run_at, idx = s.insert_event(event, trigger_time=10.0, category="test")
        assert run_at == start + timedelta(seconds=10.0)
        assert event.category == "test"
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

    def test_insert_event_with_category(self):
        """insert_event should set event category."""
        s = Scheduler()
        event = Event(data={"test": 4})
        s.insert_event(event, trigger_time=5.0, category="growth")
        assert event.category == "growth"

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

    def test_insert_event_with_callback(self):
        """insert_event should accept optional callback."""
        s = Scheduler()
        event = Event(data={"test": 7})
        results = []
        def callback():
            results.append("called")
        s.insert_event(event, trigger_time=1.0, callback=callback)
        s.step()
        assert results == ["called"]


class TestPopEventMethod:
    """Test the pop_event method."""

    def test_pop_event_empty_queue(self):
        """pop_event should return None on empty queue."""
        s = Scheduler()
        result = s.pop_event()
        assert result is None

    def test_pop_event_no_category_filter(self):
        """pop_event with no category should return earliest event."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        s.insert_event(event3, trigger_time=3.0, category="cat1")
        s.insert_event(event1, trigger_time=1.0, category="cat1")
        s.insert_event(event2, trigger_time=2.0, category="cat1")
        popped = s.pop_event()
        assert popped.data["id"] == 1

    def test_pop_event_with_category_filter(self):
        """pop_event with category should return earliest event in that category."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        s.insert_event(event1, trigger_time=1.0, category="weather")
        s.insert_event(event2, trigger_time=2.0, category="growth")
        s.insert_event(event3, trigger_time=3.0, category="weather")
        popped = s.pop_event(category="weather")
        assert popped.data["id"] == 1

    def test_pop_event_category_not_found(self):
        """pop_event with non-matching category should return None."""
        s = Scheduler()
        event = Event(data={"id": 1})
        s.insert_event(event, trigger_time=1.0, category="weather")
        popped = s.pop_event(category="nonexistent")
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
        event1 = Event(data={"id": 1})
        event2 = Event(data={"id": 2})
        event3 = Event(data={"id": 3})
        event4 = Event(data={"id": 4})
        s.insert_event(event1, trigger_time=1.0, category="cat1")
        s.insert_event(event2, trigger_time=2.0, category="cat2")
        s.insert_event(event3, trigger_time=3.0, category="cat1")
        s.insert_event(event4, trigger_time=4.0, category="cat2")
        # Pop cat1 events, leaving cat2 intact
        popped = s.pop_event(category="cat1")
        assert popped.data["id"] == 1
        # cat2 events should still be in order
        popped = s.pop_event(category="cat2")
        assert popped.data["id"] == 2
        popped = s.pop_event(category="cat2")
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
        s.schedule(5.0, lambda: None)
        s.step()
        assert s.now == start + timedelta(seconds=5.0)

    def test_step_executes_callback(self):
        """step should execute the scheduled callback."""
        s = Scheduler()
        results = []
        s.schedule(1.0, lambda x: results.append(x), "test_arg")
        s.step()
        assert results == ["test_arg"]

    def test_step_returns_callback_result(self):
        """step should return the callback's return value."""
        s = Scheduler()
        s.schedule(1.0, lambda: "result_value")
        result = s.step()
        assert result == "result_value"

    def test_step_multiple_calls(self):
        """Multiple step calls should process events in order."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        times = []
        s.schedule(1.0, lambda: times.append(s.now))
        s.schedule(2.0, lambda: times.append(s.now))
        s.schedule(3.0, lambda: times.append(s.now))
        s.step()
        s.step()
        s.step()
        assert times[0] == start + timedelta(seconds=1.0)
        assert times[1] == start + timedelta(seconds=2.0)
        assert times[2] == start + timedelta(seconds=3.0)

    def test_run_empty_queue(self):
        """run on empty queue should not error."""
        s = Scheduler()
        s.run()  # Should complete without error

    def test_run_processes_all_events(self):
        """run should process all scheduled events."""
        s = Scheduler()
        results = []
        s.schedule(1.0, lambda: results.append(1))
        s.schedule(2.0, lambda: results.append(2))
        s.schedule(3.0, lambda: results.append(3))
        s.run()
        assert results == [1, 2, 3]

    def test_run_with_until_time(self):
        """run(until=T) should stop processing events after time T."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        results = []
        s.schedule(1.0, lambda: results.append(1))
        s.schedule(2.0, lambda: results.append(2))
        s.schedule(3.0, lambda: results.append(3))
        until_time = start + timedelta(seconds=2.5)
        s.run(until=until_time)
        assert results == [1, 2]
        assert s.now == until_time

    def test_run_advances_time_to_until(self):
        """run(until=T) should advance now to T even if no events fire after."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(1.0, lambda: None)
        until_time = start + timedelta(seconds=5.0)
        s.run(until=until_time)
        assert s.now == until_time


class TestEventOrdering:
    """Test that events maintain proper chronological ordering."""

    def test_events_processed_in_chronological_order(self):
        """Events should be processed in chronological order regardless of insertion order."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        times = []

        # Insert events out of order
        s.schedule(5.0, lambda: times.append(s.now))
        s.schedule(1.0, lambda: times.append(s.now))
        s.schedule(3.0, lambda: times.append(s.now))
        s.schedule(2.0, lambda: times.append(s.now))

        s.run()

        assert times[0] == start + timedelta(seconds=1.0)
        assert times[1] == start + timedelta(seconds=2.0)
        assert times[2] == start + timedelta(seconds=3.0)
        assert times[3] == start + timedelta(seconds=5.0)

    def test_events_with_same_time_use_insertion_order(self):
        """Events with same trigger time should use insertion order (idx tie-breaker)."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        results = []

        s.schedule(1.0, lambda: results.append("a"))
        s.schedule(1.0, lambda: results.append("b"))
        s.schedule(1.0, lambda: results.append("c"))

        s.run()

        assert results == ["a", "b", "c"]


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

