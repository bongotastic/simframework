import datetime
from datetime import timedelta

try:
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.scope import Scope
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scheduler import Scheduler
    from simframework.event import Event
    from simframework.scope import Scope


def test_peek_events_filter_by_scope_descendants():
    s = Scheduler()
    root = Scope("personnel")
    child = Scope("eva", parent=root)

    e_root = Event(data={"id": "root"})
    e_child = Event(data={"id": "child"})

    s.insert_event(e_root, trigger_time=1.0, scope=root)
    s.insert_event(e_child, trigger_time=2.0, scope=child)

    # By default peek_events should include descendants
    peeked = s.peek_events(scope=root)
    assert [ev.data["id"] for _, ev in peeked] == ["root", "child"]

    # If include_descendants is False, only root should be returned
    peeked_no_desc = s.peek_events(scope=root, include_descendants=False)
    assert [ev.data["id"] for _, ev in peeked_no_desc] == ["root"]
