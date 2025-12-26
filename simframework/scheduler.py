"""A simple discrete-event scheduler for simulations.

This core is intentionally minimal and synchronous; it keeps a monotonic simulation
`now` time as a `datetime.datetime` and an event queue. Later we can extend this to
support stochastic events, priorities, distributed scheduling, or generative-AI-driven
event handlers.
"""
from heapq import heappush, heappop
from typing import Callable, Any, List, Tuple, Optional, Union, TYPE_CHECKING
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
    from .system import SystemInstance


class Scheduler:
    """Discrete-event scheduler using real date/time moments.

    Time is stored as a `datetime.datetime`. `schedule` accepts either a number
    of seconds (float) or a `datetime.timedelta` for the delay. `now` can be
    read or set via the property.

    Methods:
    - `schedule(delay, callback, *args, **kwargs)`: schedule callback after `delay`.
    - `step()`: execute the next scheduled event and advance time.
    - `run(until=None)`: run until queue empty or until datetime `until`.
    """

    def __init__(self, start_time: Optional[datetime.datetime] = None):
        if start_time is None:
            start_time = datetime.datetime.now()
        if not isinstance(start_time, datetime.datetime):
            raise TypeError("start_time must be a datetime.datetime if provided")

        self._time: datetime.datetime = start_time
        self._queue: List[Tuple[datetime.datetime, int, Tuple[Callable[..., Any], tuple, dict]]] = []
        self._counter: int = 0

    @property
    def now(self) -> datetime.datetime:
        return self._time

    @now.setter
    def now(self, value: datetime.datetime) -> None:
        if not isinstance(value, datetime.datetime):
            raise TypeError("now must be a datetime.datetime")
        self._time = value

    def schedule(self, delay: Union[float, datetime.timedelta, datetime.datetime], callback: Callable[..., Any], *args, event: Optional[Event] = None, **kwargs) -> Tuple[datetime.datetime, int]:
        """Schedule `callback` to run at a specific time or after a delay.

        `delay` may be:
        - an absolute `datetime.datetime` (trigger time independent of scheduler's now)
        - a float (seconds relative to scheduler's now)
        - a `datetime.timedelta` (relative to scheduler's now)

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
            event = Event(data={"args": args, "kwargs": kwargs})
        heappush(self._queue, (run_at, self._counter, (callback, event)))
        self._counter += 1
        return run_at, self._counter - 1

    def insert_event(self, event: Event, trigger_time: Union[datetime.datetime, float, datetime.timedelta], category: Optional[str] = None, callback: Optional[Callable[..., Any]] = None, *, scope: Optional["Scope"] = None, system: Optional["SystemInstance"] = None) -> Tuple[datetime.datetime, int]:
        """Insert a pre-built `Event` into the scheduler.

        - `event`: an instance of `Event`.
        - `trigger_time`: either an absolute `datetime.datetime`, a number of seconds
          (float/int) relative to the scheduler's `now`, or a `datetime.timedelta`
          relative to the scheduler's `now`.
        - `category`: optional label stored on the event.
        - `callback`: optional callable to run when the event fires. If omitted,
          the scheduler will use a no-op handler that returns the `Event`.

        Returns the scheduled run time and an integer id.
        """
        if not isinstance(event, Event):
            raise TypeError("event must be an Event instance")

        if category is not None:
            event.category = category
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

        if callback is None:
            def _default_noop(*_a, **_k):
                return event
            cb = _default_noop
        else:
            cb = callback

        heappush(self._queue, (run_at, self._counter, (cb, event)))
        self._counter += 1
        return run_at, self._counter - 1

    def pop_event(self, category: Optional[str] = None) -> Optional[Event]:
        """Remove and return the next scheduled Event.

        If `category` is provided, the scheduler searches chronologically for the
        next event whose `Event.category` matches the value and removes it from
        the queue. If no matching event exists, returns `None`.
        """
        if not self._queue:
            return None

        temp: List[Tuple[datetime.datetime, int, Tuple[Callable[..., Any], Event]]] = []
        found_event: Optional[Event] = None

        # Pop items until we find a matching category/system (or run out).
        # Keep others in temp so we can push them back preserving heap order.
        while self._queue:
            run_at, idx, (cb, event) = heappop(self._queue)
            matches_category = category is None or event.category == category
            # system filter may be provided via kwargs; callers can extend to
            # support scope filtering similarly in future.
            matches_system = True
            # If caller passed a 'system' object via temporary attribute in
            # the provided category parameter (deprecated), allow matching.
            # For clarity, prefer an explicit system-aware pop API in future.
            if hasattr(self, "_pop_system_filter") and self._pop_system_filter is not None:
                matches_system = event.system == self._pop_system_filter

            if matches_category and matches_system:
                found_event = event
                break
            temp.append((run_at, idx, (cb, event)))

        # Push back any items we removed that were not the target.
        for item in temp:
            heappush(self._queue, item)

        # Clear any temporary system filter state if set
        if hasattr(self, "_pop_system_filter"):
            self._pop_system_filter = None

        return found_event

    def pop_event_for_system(self, system: "SystemInstance", category: Optional[str] = None) -> Optional[Event]:
        """Convenience method: pop next event for a specific `system`.

        This searches chronologically for the next event whose `Event.system`
        equals `system`, optionally also matching `category`.
        """
        # Set a temporary filter checked by `pop_event` to avoid duplicating
        # the search logic. This is safe for single-threaded synchronous use.
        self._pop_system_filter = system
        return self.pop_event(category=category)

    def step(self) -> Optional[Any]:
        if not self._queue:
            return None
        run_at, _idx, (callback, event) = heappop(self._queue)
        self._time = run_at
        # Call the callback with args/kwargs stored inside Event.data for
        # backwards compatibility with previous API usage.
        ev_args = event.data.get("args", ())
        ev_kwargs = event.data.get("kwargs", {})
        return callback(*ev_args, **ev_kwargs)

    def run(self, until: Optional[datetime.datetime] = None) -> None:
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
            self.step()

        if until is not None and self._time < until:
            self._time = until

    def peek_events(self, category: Optional[str] = None, scope: Optional["Scope"] = None, system: Optional["SystemInstance"] = None, limit: Optional[int] = None) -> List[Event]:
        """Look ahead at upcoming events without modifying the queue.

        Returns a list of Event objects in chronological order, optionally filtered
        by category, scope, or system. If multiple filters are provided, all must match.

        Args:
            category: Optional category to filter by.
            scope: Optional Scope object to filter by.
            system: Optional SystemInstance to filter by.
            limit: Optional maximum number of events to return.

        Returns:
            A list of Event objects matching the filters (or empty if none match).
        """
        result = []
        for run_at, idx, (cb, event) in self._queue:
            # Check all filters
            if category is not None and event.category != category:
                continue
            if scope is not None and event.scope != scope:
                continue
            if system is not None and event.system != system:
                continue

            result.append(event)

            # Stop if limit reached
            if limit is not None and len(result) >= limit:
                break

        return result
