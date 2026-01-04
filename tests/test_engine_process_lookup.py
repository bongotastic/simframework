from pathlib import Path

from simframework.engine import SimulationEngine


def test_get_process_lookup_variants():
    engine = SimulationEngine()

    # Full path lookup
    p1 = engine.get_process("process/cultivation/sowing")
    assert p1 is not None
    assert p1.path == "process/cultivation/sowing"

    # Exact name lookup
    p2 = engine.get_process("Generic Sowing")
    assert p2 is not None
    assert p2.path == "process/cultivation/sowing"

    # Suffix lookup
    p3 = engine.get_process("sowing")
    assert p3 is not None
    assert p3.path == "process/cultivation/sowing"

    # Substring lookup (case-insensitive)
    p4 = engine.get_process("milling")
    assert p4 is not None
    assert "milling_wheat" in p4.path

    # Non-existent returns None
    assert engine.get_process("this-does-not-exist") is None
