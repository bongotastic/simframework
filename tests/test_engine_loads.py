from pathlib import Path

from simframework.engine import SimulationEngine


def test_engine_loads_demesne_domain_and_processes():
    pkg_root = Path(__file__).resolve().parents[1]
    domain_file = pkg_root / "simulations" / "Demesne" / "domain.yaml"
    proc_file = pkg_root / "simulations" / "Demesne" / "domain_processes.yaml"
    assert domain_file.exists()
    assert proc_file.exists()

    engine = SimulationEngine()
    # Domain should be loaded
    assert engine.domain is not None
    assert engine.domain.name == "Demesne"

    # Processes should be loaded and include known paths
    assert isinstance(engine.processes, dict)
    assert "process/cultivation/sowing" in engine.processes
    assert "process/processing/milling_wheat" in engine.processes
    assert len(engine.processes) >= 10
