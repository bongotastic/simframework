import datetime
from datetime import timedelta
import re

from simframework.engine import SimulationEngine
from simframework.event import Event


def test_print_status_shows_counts_and_times(capsys):
    engine = SimulationEngine(start_time=datetime.datetime(2025, 1, 1, 0, 0, 0))
    base = engine.scheduler.now

    # schedule 3 events at 1s, 3s, 2s
    e1 = Event(data={"event_id": 1})
    e2 = Event(data={"event_id": 2})
    e3 = Event(data={"event_id": 3})
    engine.scheduler.schedule(1.0, event=e1)
    engine.scheduler.schedule(3.0, event=e2)
    engine.scheduler.schedule(2.0, event=e3)

    engine.print_status()
    out = capsys.readouterr().out

    # count line
    assert "3 event(s) in queue" in out

    # next should be base + 1s, last = base + 3s
    assert "Next event:" in out
    assert "Last  event:" in out
    assert (base + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S") in out
    assert (base + timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S") in out

    # check table has three event lines with ids 1,2,3
    ids = re.findall(r"^\s*(\d+)\s*\|", out, flags=re.M)
    assert set(ids) == {"1", "2", "3"}


def test_print_status_empty_queue(capsys):
    engine = SimulationEngine(start_time=datetime.datetime(2025, 1, 1, 0, 0, 0))
    engine.print_status()
    out = capsys.readouterr().out
    assert "0 event(s) in queue" in out
    assert "Next event:" not in out
    assert "Events:" in out
