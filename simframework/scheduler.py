"""A simple discrete-event scheduler for simulations.

This core is intentionally minimal and synchronous; it keeps a monotonic simulation
`now` time as a `datetime.datetime` and an event queue. Later we can extend this to
support stochastic events, priorities, distributed scheduling, or generative-AI-driven
event handlers.
"""
from heapq import heappush, heappop
from typing import Any, Dict, List, Set, Tuple, Optional, Union, TYPE_CHECKING
import datetime

try:
    # Prefer absolute import when package is installed or run with -m
    from simframework.event import Event
except ImportError:
    # Fallback for running the package in environments where absolute imports
    # don't resolve (e.g., some test/debug runs).
    from .event import Event

if TYPE_CHECKING:
    from .scope import Scope
    from .entity import Entity


class Scheduler:
    """Discrete-event scheduler using real date/time moments.

    Time is stored as a `datetime.datetime`. `schedule` accepts either a number
    of seconds (float) or a `datetime.timedelta` for the delay. `now` can be
    read or set via the property.

    Methods:
    - `schedule(delay, **data)`: schedule an event after `delay`.
    - `step()`: execute the next scheduled event and advance time.
    - `run(until=None)`: run until queue empty or until datetime `until`.
    - `get_events(scope, system)`: retrieve events filtered by scope/system.
    - `delete_events(scope, system)`: cancel events (lazy deletion).
    - `reschedule_event(event_id, delta)`: reschedule event by a time delta.
    - `cleanup()`: remove cancelled events from the heap.
    """

    def __init__(self, start_time: Optional[datetime.datetime] = None):
        if start_time is None:
            start_time = datetime.datetime.now()
        if not isinstance(start_time, datetime.datetime):
            raise TypeError("start_time must be a datetime.datetime if provided")

        self._time: datetime.datetime = start_time
        # Queue stores (run_at, counter, event)
        self._queue: List[Tuple[datetime.datetime, int, Event]] = []
        self._counter: int = 0
        # Lazy deletion: track cancelled event IDs
        self._cancelled: Set[int] = set()
        # Map event_id -> (run_at, event) for reschedule lookups
        self._event_map: Dict[int, Tuple[datetime.datetime, Event]] = {}

    @property
    def now(self) -> datetime.datetime:
        return self._time

    @now.setter
    def now(self, value: datetime.datetime) -> None:
        if not isinstance(value, datetime.datetime):
            raise TypeError("now must be a datetime.datetime")
        self._time = value

    def schedule(self, delay: Union[float, datetime.timedelta, datetime.datetime], event: Optional[Event] = None, **data) -> Tuple[datetime.datetime, int]:
        """Schedule an event to run at a specific time or after a delay.

        `delay` may be:
        - an absolute `datetime.datetime` (trigger time independent of scheduler's now)
        - a float (seconds relative to scheduler's now)
        - a `datetime.timedelta` (relative to scheduler's now)

        If `event` is not provided, a new `Event` is created with `data` as its payload.

        Returns the scheduled run time and an integer id.
        """
        if isinstance(delay, datetime.datetime):
            # Absolute trigger time, independent of _time
            run_at = delay
        elif isinstance(delay, (int, float)):
            if delay < 0:
                raise ValueError("delay must be >= 0")
            delta = datetime.timedelta(seconds=float(delay))
            run_at = self._time + delta
        elif isinstance(delay, datetime.timedelta):
            if delay.total_seconds() < 0:
                raise ValueError("delay must be >= 0")
            run_at = self._time + delay
        else:
            raise TypeError("delay must be datetime, float seconds, or timedelta")

        if event is None:
            event = Event(data=data)
        
        event_id = self._counter
        heappush(self._queue, (run_at, event_id, event))
        self._event_map[event_id] = (run_at, event)
        self._counter += 1
        return run_at, event_id

    def insert_event(self, event: Event, trigger_time: Union[datetime.datetime, float, datetime.timedelta], *, scope: Optional["Scope"] = None, system: Optional["Entity"] = None) -> Tuple[datetime.datetime, int]:
        """Insert a pre-built `Event` into the scheduler.

        - `event`: an instance of `Event`.
        - `trigger_time`: either an absolute `datetime.datetime`, a number of seconds
          (float/int) relative to the scheduler's `now`, or a `datetime.timedelta`
          relative to the scheduler's `now`.

        Optional `scope` and `system` can be attached to the event for later
        filtering when peeking or popping events.

        Returns the scheduled run time and an integer id.
        """
        if not isinstance(event, Event):
            raise TypeError("event must be an Event instance")

        if scope is not None:
            event.scope = scope
        if system is not None:
            event.system = system

        if isinstance(trigger_time, datetime.datetime):
            run_at = trigger_time
        elif isinstance(trigger_time, (int, float)):
            if trigger_time < 0:
                raise ValueError("trigger_time seconds must be >= 0")
            run_at = self._time + datetime.timedelta(seconds=float(trigger_time))
        elif isinstance(trigger_time, datetime.timedelta):
            if trigger_time.total_seconds() < 0:
                raise ValueError("trigger_time timedelta must be >= 0")
            run_at = self._time + trigger_time
        else:
            raise TypeError("trigger_time must be datetime, seconds (float/int), or timedelta")

        event_id = self._counter
        heappush(self._queue, (run_at, event_id, event))
        self._event_map[event_id] = (run_at, event)
        self._counter += 1
        return run_at, event_id

    def pop_event(self, scope: Optional["Scope"] = None, *, system: Optional["Entity"] = None, include_descendants: bool = False) -> Optional[Event]:
        """Remove and return the next scheduled Event.

        If `scope` is provided, the scheduler searches chronologically for the
        next event whose `Event.scope` equals the provided `scope` and removes
        it from the queue. When `include_descendants` is True, events whose
        `Event.scope` is a descendant of `scope` also match. System filtering
        is also supported. If no matching event exists, returns `None`.
        """
        if not self._queue:
            return None

        temp: List[Tuple[datetime.datetime, int, Event]] = []
        found_event: Optional[Event] = None
        found_idx: Optional[int] = None

        # Pop items until we find a matching scope/system (or run out).
        # Keep others in temp so we can push them back preserving heap order.
        while self._queue:
            run_at, idx, event = heappop(self._queue)
            
            # Skip cancelled events (lazy deletion)
            if idx in self._cancelled:
                self._cancelled.discard(idx)
                self._event_map.pop(idx, None)
                continue
            
            # Scope matching supports optional descendant inclusion
            if scope is None:
                matches_scope = True
            else:
                if event.scope is None:
                    matches_scope = False
                elif include_descendants:
                    matches_scope = (event.scope == scope) or scope.is_ancestor_of(event.scope)
                else:
                    matches_scope = event.scope == scope

            matches_system = True
            if system is not None:
                # Entities are matched by identity equality. Hierarchical
                # descendant matching was removed along with systems/agents.
                matches_system = event.system == system

            if matches_scope and matches_system:
                found_event = event
                found_idx = idx
                break
            temp.append((run_at, idx, event))

        # Push back any items we removed that were not the target.
        for item in temp:
            heappush(self._queue, item)

        # Clean up tracking for the popped event
        if found_idx is not None:
            self._event_map.pop(found_idx, None)

        return found_event

    def pop_event_for_system(self, system: "Entity", *, include_descendants: bool = False) -> Optional[Event]:
        """Convenience method: pop next event for a specific `system`.

        This searches chronologically for the next event whose `Event.system`
        equals `system`. When `include_descendants` is True, descendant systems
        also match.
        """
        return self.pop_event(system=system, include_descendants=False)

    def step(self) -> Optional[Event]:
        """Execute the next scheduled event and advance simulation time.
        
        Skips any events that have been cancelled (lazy deletion).
        Returns None if the queue is empty or all remaining events are cancelled.
        """
        while self._queue:
            run_at, idx, event = heappop(self._queue)
            
            # Skip cancelled events (lazy deletion)
            if idx in self._cancelled:
                self._cancelled.discard(idx)
                self._event_map.pop(idx, None)
                continue
            
            # Valid event found
            self._time = run_at
            self._event_map.pop(idx, None)
            return event
        
        return None

    def run(self, until: Optional[datetime.datetime] = None) -> Event:
        """Run events until queue empty or until the `until` datetime.

        If `until` is provided and no more events happen before `until`, the
        scheduler's `now` will be advanced to `until`.
        """
        if until is not None and not isinstance(until, datetime.datetime):
            raise TypeError("until must be a datetime.datetime or None")

        while self._queue:
            next_time = self._queue[0][0]
            if until is not None and next_time > until:
                break
            # process the next event and continue looping
            self.step()

        if until is not None and self._time < until:
            self._time = until

    def peek_events(self, scope: Optional["Scope"] = None, system: Optional["Entity"] = None, limit: Optional[int] = None, *, include_descendants: bool = True) -> List[Tuple[datetime.datetime, Event]]:
        """Look ahead at upcoming events without modifying the queue.

        Returns a list of (run_at, Event) tuples in chronological order, optionally filtered
        by scope or system. If multiple filters are provided, all must match.

        Args:
            scope: Optional Scope object to filter by. When `include_descendants` is True
                (the default), scopes that are descendants of `scope` will also match.
            system: Optional SystemInstance to filter by.
            limit: Optional maximum number of events to return.
            include_descendants: When True, descendant systems/scopes of the provided
                `system` or `scope` also match.

        Returns:
            A list of (datetime, Event) tuples matching the filters (or empty if none match).
        """
        result = []
        for run_at, idx, event in self._queue:
            # Skip cancelled events
            if idx in self._cancelled:
                continue
            
            # Scope filtering supports descendant matching when requested
            if scope is not None:
                if event.scope is None:
                    continue
                if include_descendants:
                    if not (event.scope == scope or scope.is_ancestor_of(event.scope)):
                        continue
                else:
                    if event.scope != scope:
                        continue

            # System filtering supports descendant matching when requested
            if system is not None:
                if event.system != system:
                    continue

            result.append((run_at, idx, event))

            # Stop if limit reached
            if limit is not None and len(result) >= limit:
                break

        # Return without idx for backward compatibility
        return [(run_at, event) for run_at, idx, event in result]

    def get_events(self, scope: Optional["Scope"] = None, system: Optional["Entity"] = None, *, include_descendants: bool = True) -> List[Tuple[int, datetime.datetime, Event]]:
        """Retrieve scheduled events filtered by scope and/or entity.

        Returns a list of (event_id, run_at, Event) tuples in chronological order,
        filtered by scope and/or system. Cancelled events are excluded.

        Args:
            scope: Optional Scope to filter by. When `include_descendants` is True
                (the default), scopes that are descendants also match.
            system: Optional Entity to filter by (exact match).
            include_descendants: When True, descendant scopes of `scope` also match.

        Returns:
            A list of (event_id, datetime, Event) tuples matching the filters.
        """
        result = []
        for run_at, idx, event in sorted(self._queue):
            # Skip cancelled events
            if idx in self._cancelled:
                continue
            
            # Scope filtering
            if scope is not None:
                if event.scope is None:
                    continue
                if include_descendants:
                    if not (event.scope == scope or scope.is_ancestor_of(event.scope)):
                        continue
                else:
                    if event.scope != scope:
                        continue

            # System filtering
            if system is not None:
                if event.system != system:
                    continue

            result.append((idx, run_at, event))

        return result

    def delete_events(self, scope: Optional["Scope"] = None, system: Optional["Entity"] = None, *, include_descendants: bool = True) -> int:
        """Cancel events matching the given filters (lazy deletion).

        Events are marked as cancelled but remain in the heap until they are
        naturally popped or `cleanup()` is called. Returns the count of events
        cancelled.

        Args:
            scope: Optional Scope to filter by. When `include_descendants` is True
                (the default), scopes that are descendants also match.
            system: Optional Entity to filter by (exact match).
            include_descendants: When True, descendant scopes of `scope` also match.

        Returns:
            The number of events cancelled.
        """
        if scope is None and system is None:
            raise ValueError("At least one of scope or system must be provided")

        matching = self.get_events(scope=scope, system=system, include_descendants=include_descendants)
        cancelled_count = 0
        for event_id, run_at, event in matching:
            if event_id not in self._cancelled:
                self._cancelled.add(event_id)
                cancelled_count += 1

        return cancelled_count

    def cancel_event(self, event_id: int) -> bool:
        """Cancel a single event by its ID (lazy deletion).

        The event is marked as cancelled but remains in the heap until it is
        naturally popped or `cleanup()` is called.

        Args:
            event_id: The ID returned when the event was scheduled.

        Returns:
            True if the event was found and cancelled, False if it was
            already cancelled or not found.
        """
        if event_id in self._cancelled:
            return False
        if event_id not in self._event_map:
            return False
        self._cancelled.add(event_id)
        return True

    def reschedule_event(self, event_id: int, delta: Union[float, datetime.timedelta]) -> Optional[Tuple[datetime.datetime, int]]:
        """Reschedule an event by a given time delta.

        The original event is cancelled and a new event is inserted with the
        adjusted trigger time. The new event gets a new event_id.

        Args:
            event_id: The ID of the event to reschedule.
            delta: Time adjustment - positive values move the event later,
                negative values move it earlier. Can be float (seconds) or timedelta.

        Returns:
            A tuple of (new_run_at, new_event_id) if rescheduled successfully,
            or None if the event was not found or already cancelled.
        """
        if event_id in self._cancelled:
            return None
        if event_id not in self._event_map:
            return None

        old_run_at, event = self._event_map[event_id]

        # Calculate new run time
        if isinstance(delta, (int, float)):
            delta = datetime.timedelta(seconds=float(delta))
        elif not isinstance(delta, datetime.timedelta):
            raise TypeError("delta must be float (seconds) or timedelta")

        new_run_at = old_run_at + delta

        # Cancel the old event
        self._cancelled.add(event_id)

        # Insert the event at the new time
        new_id = self._counter
        heappush(self._queue, (new_run_at, new_id, event))
        self._event_map[new_id] = (new_run_at, event)
        self._counter += 1

        return new_run_at, new_id

    def cleanup(self) -> int:
        """Remove cancelled events from the heap.

        Call this periodically if many events have been cancelled to reclaim
        memory and improve performance. This rebuilds the heap without the
        cancelled events.

        Returns:
            The number of stale events removed.
        """
        if not self._cancelled:
            return 0

        # Filter out cancelled events
        original_len = len(self._queue)
        self._queue = [
            (run_at, idx, event)
            for run_at, idx, event in self._queue
            if idx not in self._cancelled
        ]

        # Clean up tracking
        for idx in self._cancelled:
            self._event_map.pop(idx, None)

        removed_count = original_len - len(self._queue)
        self._cancelled.clear()

        # Rebuild heap structure (list comprehension doesn't preserve heap property)
        from heapq import heapify
        heapify(self._queue)

        return removed_count

    @property
    def pending_count(self) -> int:
        """Return the count of non-cancelled events in the queue."""
        return len(self._queue) - len(self._cancelled)

    @property
    def cancelled_count(self) -> int:
        """Return the count of cancelled events still in the queue."""
        return len(self._cancelled)


# Hierarchical system/descendant matching and SystemInstance types were
# removed when systems/agents were deleted; identity equality is used above.
