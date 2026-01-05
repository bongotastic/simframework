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
        # `schedule` accepts a timedelta delay in the strict API
        run_at, idx = s.schedule(timedelta(seconds=5.0))
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
        # schedule accepts a timedelta relative to `now`; convert absolute
        run_at, idx = s.schedule(absolute_time - start)
        assert run_at == absolute_time
        assert idx == 0

    def test_schedule_negative_delay_float(self):
        """schedule should reject negative float delay."""
        s = Scheduler()
        with pytest.raises(ValueError):
            s.schedule(timedelta(seconds=-1))

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
        _, idx1 = s.schedule(timedelta(seconds=1.0))
        _, idx2 = s.schedule(timedelta(seconds=2.0))
        _, idx3 = s.schedule(timedelta(seconds=3.0))
        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2

    def test_schedule_with_custom_event(self):
        """schedule should accept pre-built Event objects."""
        s = Scheduler()
        event = Event(data={"custom": "data"}, timespan=timedelta(hours=1))
        run_at, idx = s.schedule(timedelta(seconds=5.0), event=event)
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
        s.schedule(timedelta(seconds=5.0))
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
        s.schedule(timedelta(seconds=1.0))
        s.schedule(timedelta(seconds=2.0))
        s.schedule(timedelta(seconds=3.0))
        
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
        s.schedule(timedelta(seconds=1.0))
        s.schedule(timedelta(seconds=2.0))
        s.schedule(timedelta(seconds=3.0))
        s.run()
        assert s.now == start + timedelta(seconds=3.0)
        assert s.pop_event() is None

    def test_run_with_until_time(self):
        """run(until=T) should stop processing events after time T."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        s.schedule(timedelta(seconds=1.0))
        s.schedule(timedelta(seconds=2.0))
        s.schedule(timedelta(seconds=3.0))
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
        s.schedule(timedelta(seconds=1.0))
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
        s.schedule(timedelta(seconds=5.0))
        s.schedule(timedelta(seconds=1.0))
        s.schedule(timedelta(seconds=3.0))
        s.schedule(timedelta(seconds=2.0))

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
        
        s.schedule(timedelta(seconds=1.0), event=Event(data={"id": "a"}))
        s.schedule(timedelta(seconds=1.0), event=Event(data={"id": "b"}))
        s.schedule(timedelta(seconds=1.0), event=Event(data={"id": "c"}))

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


class TestGetEvents:
    """Test the get_events method for filtered event retrieval."""

    def test_get_events_empty_queue(self):
        """get_events should return empty list on empty queue."""
        s = Scheduler()
        result = s.get_events()
        assert result == []

    def test_get_events_no_filter(self):
        """get_events with no filter should return all events."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        s.insert_event(e3, trigger_time=3.0)
        result = s.get_events()
        assert len(result) == 3
        # Events should be in chronological order
        assert result[0][2].data["id"] == 1
        assert result[1][2].data["id"] == 2
        assert result[2][2].data["id"] == 3

    def test_get_events_with_scope_filter(self):
        """get_events with scope filter should return only matching events."""
        s = Scheduler()
        from simframework.scope import Scope
        scope_weather = Scope("weather")
        scope_growth = Scope("growth")
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        s.insert_event(e1, trigger_time=1.0, scope=scope_weather)
        s.insert_event(e2, trigger_time=2.0, scope=scope_growth)
        s.insert_event(e3, trigger_time=3.0, scope=scope_weather)
        result = s.get_events(scope=scope_weather)
        assert len(result) == 2
        assert result[0][2].data["id"] == 1
        assert result[1][2].data["id"] == 3

    def test_get_events_with_system_filter(self):
        """get_events with system filter should return only matching events."""
        s = Scheduler()
        from simframework.entity import Entity
        entity1 = Entity("entity1")
        entity2 = Entity("entity2")
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        s.insert_event(e1, trigger_time=1.0, system=entity1)
        s.insert_event(e2, trigger_time=2.0, system=entity2)
        s.insert_event(e3, trigger_time=3.0, system=entity1)
        result = s.get_events(system=entity1)
        assert len(result) == 2
        assert result[0][2].data["id"] == 1
        assert result[1][2].data["id"] == 3

    def test_get_events_returns_event_id(self):
        """get_events should return event_id in the tuple."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        _, event_id = s.insert_event(e1, trigger_time=1.0)
        result = s.get_events()
        assert len(result) == 1
        assert result[0][0] == event_id

    def test_get_events_excludes_cancelled(self):
        """get_events should not return cancelled events."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        s.cancel_event(id1)
        result = s.get_events()
        assert len(result) == 1
        assert result[0][2].data["id"] == 2


class TestCancelEvent:
    """Test the cancel_event method for single event cancellation."""

    def test_cancel_event_basic(self):
        """cancel_event should mark event as cancelled."""
        s = Scheduler()
        e = Event(data={"id": 1})
        _, event_id = s.insert_event(e, trigger_time=1.0)
        result = s.cancel_event(event_id)
        assert result is True
        assert event_id in s._cancelled

    def test_cancel_event_already_cancelled(self):
        """cancel_event should return False if already cancelled."""
        s = Scheduler()
        e = Event(data={"id": 1})
        _, event_id = s.insert_event(e, trigger_time=1.0)
        s.cancel_event(event_id)
        result = s.cancel_event(event_id)
        assert result is False

    def test_cancel_event_not_found(self):
        """cancel_event should return False for non-existent event."""
        s = Scheduler()
        result = s.cancel_event(999)
        assert result is False

    def test_step_skips_cancelled_event(self):
        """step should skip cancelled events."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        s.cancel_event(id1)
        result = s.step()
        assert result.data["id"] == 2

    def test_step_returns_none_when_all_cancelled(self):
        """step should return None if all events are cancelled."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        _, id2 = s.insert_event(e2, trigger_time=2.0)
        s.cancel_event(id1)
        s.cancel_event(id2)
        result = s.step()
        assert result is None


class TestDeleteEvents:
    """Test the delete_events method for batch cancellation."""

    def test_delete_events_by_scope(self):
        """delete_events should cancel all events in a scope."""
        s = Scheduler()
        from simframework.scope import Scope
        scope_weather = Scope("weather")
        scope_growth = Scope("growth")
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        s.insert_event(e1, trigger_time=1.0, scope=scope_weather)
        s.insert_event(e2, trigger_time=2.0, scope=scope_growth)
        s.insert_event(e3, trigger_time=3.0, scope=scope_weather)
        count = s.delete_events(scope=scope_weather)
        assert count == 2
        # Only growth event should remain
        result = s.get_events()
        assert len(result) == 1
        assert result[0][2].data["id"] == 2

    def test_delete_events_by_system(self):
        """delete_events should cancel all events for a system."""
        s = Scheduler()
        from simframework.entity import Entity
        entity1 = Entity("entity1")
        entity2 = Entity("entity2")
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        s.insert_event(e1, trigger_time=1.0, system=entity1)
        s.insert_event(e2, trigger_time=2.0, system=entity2)
        s.insert_event(e3, trigger_time=3.0, system=entity1)
        count = s.delete_events(system=entity1)
        assert count == 2
        result = s.get_events()
        assert len(result) == 1
        assert result[0][2].data["id"] == 2

    def test_delete_events_requires_filter(self):
        """delete_events should raise ValueError if no filter provided."""
        s = Scheduler()
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0)
        with pytest.raises(ValueError):
            s.delete_events()

    def test_delete_events_returns_zero_when_no_match(self):
        """delete_events should return 0 if no events match."""
        s = Scheduler()
        from simframework.scope import Scope
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0, scope=Scope("weather"))
        count = s.delete_events(scope=Scope("nonexistent"))
        assert count == 0


class TestRescheduleEvent:
    """Test the reschedule_event method."""

    def test_reschedule_event_positive_delta_seconds(self):
        """reschedule_event should move event later with positive delta."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        e = Event(data={"id": 1})
        original_run_at, event_id = s.insert_event(e, trigger_time=10.0)
        result = s.reschedule_event(event_id, 5.0)
        assert result is not None
        new_run_at, new_id = result
        assert new_run_at == start + timedelta(seconds=15.0)
        assert new_id != event_id  # New ID assigned
        # Old event should be cancelled
        assert event_id in s._cancelled

    def test_reschedule_event_negative_delta(self):
        """reschedule_event should move event earlier with negative delta."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=10.0)
        result = s.reschedule_event(0, timedelta(seconds=-3))
        assert result is not None
        new_run_at, new_id = result
        assert new_run_at == start + timedelta(seconds=7.0)

    def test_reschedule_event_with_timedelta(self):
        """reschedule_event should accept timedelta."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=10.0)
        result = s.reschedule_event(0, timedelta(hours=1))
        assert result is not None
        new_run_at, _ = result
        assert new_run_at == start + timedelta(seconds=10.0) + timedelta(hours=1)

    def test_reschedule_event_not_found(self):
        """reschedule_event should return None for non-existent event."""
        s = Scheduler()
        result = s.reschedule_event(999, 5.0)
        assert result is None

    def test_reschedule_event_already_cancelled(self):
        """reschedule_event should return None for cancelled event."""
        s = Scheduler()
        e = Event(data={"id": 1})
        _, event_id = s.insert_event(e, trigger_time=10.0)
        s.cancel_event(event_id)
        result = s.reschedule_event(event_id, 5.0)
        assert result is None

    def test_reschedule_event_invalid_delta_type(self):
        """reschedule_event should raise TypeError for invalid delta."""
        s = Scheduler()
        e = Event(data={"id": 1})
        _, event_id = s.insert_event(e, trigger_time=10.0)
        with pytest.raises(TypeError):
            s.reschedule_event(event_id, "5 seconds")

    def test_reschedule_preserves_event_data(self):
        """reschedule_event should preserve the original event."""
        s = Scheduler()
        from simframework.scope import Scope
        scope = Scope("test")
        e = Event(data={"id": 1, "important": True})
        _, event_id = s.insert_event(e, trigger_time=10.0, scope=scope)
        s.reschedule_event(event_id, 5.0)
        # Step to get the rescheduled event
        result = s.step()
        assert result.data["id"] == 1
        assert result.data["important"] is True
        assert result.scope == scope


class TestCleanup:
    """Test the cleanup method."""

    def test_cleanup_removes_cancelled_events(self):
        """cleanup should remove cancelled events from the heap."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        _, id3 = s.insert_event(e3, trigger_time=3.0)
        s.cancel_event(id1)
        s.cancel_event(id3)
        assert len(s._queue) == 3
        removed = s.cleanup()
        assert removed == 2
        assert len(s._queue) == 1

    def test_cleanup_clears_cancelled_set(self):
        """cleanup should clear the cancelled set."""
        s = Scheduler()
        e = Event(data={"id": 1})
        _, event_id = s.insert_event(e, trigger_time=1.0)
        s.cancel_event(event_id)
        assert len(s._cancelled) == 1
        s.cleanup()
        assert len(s._cancelled) == 0

    def test_cleanup_preserves_heap_order(self):
        """cleanup should preserve chronological order."""
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        s = Scheduler(start_time=start)
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        e4 = Event(data={"id": 4})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        _, id3 = s.insert_event(e3, trigger_time=3.0)
        s.insert_event(e4, trigger_time=4.0)
        s.cancel_event(id1)
        s.cancel_event(id3)
        s.cleanup()
        # Remaining events should be in order
        result1 = s.step()
        assert result1.data["id"] == 2
        result2 = s.step()
        assert result2.data["id"] == 4

    def test_cleanup_returns_zero_when_nothing_cancelled(self):
        """cleanup should return 0 if nothing cancelled."""
        s = Scheduler()
        e = Event(data={"id": 1})
        s.insert_event(e, trigger_time=1.0)
        removed = s.cleanup()
        assert removed == 0


class TestPendingAndCancelledCount:
    """Test the pending_count and cancelled_count properties."""

    def test_pending_count_basic(self):
        """pending_count should return non-cancelled event count."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        e3 = Event(data={"id": 3})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        s.insert_event(e2, trigger_time=2.0)
        s.insert_event(e3, trigger_time=3.0)
        assert s.pending_count == 3
        s.cancel_event(id1)
        assert s.pending_count == 2

    def test_cancelled_count_basic(self):
        """cancelled_count should return cancelled event count."""
        s = Scheduler()
        e1 = Event(data={"id": 1})
        e2 = Event(data={"id": 2})
        _, id1 = s.insert_event(e1, trigger_time=1.0)
        _, id2 = s.insert_event(e2, trigger_time=2.0)
        assert s.cancelled_count == 0
        s.cancel_event(id1)
        assert s.cancelled_count == 1
        s.cancel_event(id2)
        assert s.cancelled_count == 2
