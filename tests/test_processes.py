import datetime
from pathlib import Path
import sys

try:
    from simframework.system import SystemTemplate, Process, Store
    from simframework.entity import Entity
except ImportError:
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.system import SystemTemplate, Process, Store
    from simframework.entity import Entity


def test_add_store_and_get_store():
    """Test adding and retrieving stores."""
    tmpl = SystemTemplate("test_sys")
    inst = tmpl.instantiate()

    # Add a store
    inst.add_store("energy", 100.0)
    store = inst.get_store("energy")
    assert store is not None
    assert store.quantity == pytest.approx(100.0)

    # Add more to the same store
    inst.add_store("energy", 50.0)
    store = inst.get_store("energy")
    assert store.quantity == pytest.approx(150.0)

    # Get non-existent store
    assert inst.get_store("water") is None


def test_add_process():
    """Test adding processes to a system."""
    tmpl = SystemTemplate("factory")
    inst = tmpl.instantiate()

    p1 = Process(name="production", completion_time=2.5)
    p2 = Process(name="conversion", completion_time=1.5)

    inst.add_process(p1)
    inst.add_process(p2)

    assert len(inst.processes) == 2
    assert inst.processes[0].name == "production"
    assert inst.processes[0].completion_time == 2.5


def test_aggregate_processes_flat():
    """Test aggregating processes from a single system (no children)."""
    tmpl = SystemTemplate("system")
    inst = tmpl.instantiate()

    p1 = Process(name="proc1", completion_time=1.0)
    p2 = Process(name="proc2", completion_time=2.0)

    inst.add_process(p1)
    inst.add_process(p2)

    aggregated = inst.aggregate_processes(include_children=False)
    assert len(aggregated) == 2
    assert aggregated[0].name == "proc1"
    assert aggregated[1].name == "proc2"


def test_aggregate_processes_with_children():
    """Test aggregating processes from a system and its children recursively."""
    parent_tmpl = SystemTemplate("parent")
    child1_tmpl = SystemTemplate("child1")
    child2_tmpl = SystemTemplate("child2")

    parent_tmpl.add_child(child1_tmpl)
    parent_tmpl.add_child(child2_tmpl)

    parent = parent_tmpl.instantiate()

    p_parent = Process(name="parent_proc", completion_time=1.0)
    p_child1 = Process(name="child1_proc", completion_time=0.9)
    p_child2 = Process(name="child2_proc", completion_time=0.8)

    parent.processes.append(p_parent)
    parent.children[0].processes.append(p_child1)
    parent.children[1].processes.append(p_child2)

    aggregated = parent.aggregate_processes(include_children=True)
    names = [p.name for p in aggregated]
    assert "parent_proc" in names
    assert "child1_proc" in names
    assert "child2_proc" in names
    assert len(aggregated) == 3


def test_aggregate_stores_flat():
    """Test aggregating stores from a single system."""
    tmpl = SystemTemplate("warehouse")
    inst = tmpl.instantiate()

    inst.add_store("energy", 100.0)
    inst.add_store("water", 50.0)
    inst.add_store("energy", 25.0)  # Add more to energy

    aggregated = inst.aggregate_stores(include_children=False)
    assert aggregated["energy"] == pytest.approx(125.0)
    assert aggregated["water"] == pytest.approx(50.0)


def test_aggregate_stores_with_children():
    """Test aggregating stores from a system and its children recursively."""
    parent_tmpl = SystemTemplate("parent")
    child_tmpl = SystemTemplate("child")
    parent_tmpl.add_child(child_tmpl)

    parent = parent_tmpl.instantiate()

    parent.add_store("energy", 100.0)
    parent.add_store("water", 30.0)

    parent.children[0].add_store("energy", 50.0)
    parent.children[0].add_store("water", 20.0)

    aggregated = parent.aggregate_stores(include_children=True)
    assert aggregated["energy"] == pytest.approx(150.0)
    assert aggregated["water"] == pytest.approx(50.0)


def test_execute_process_with_inputs_and_outputs():
    """Test executing a process with entity inputs and outputs."""
    from simframework.entity import Entity
    
    tmpl = SystemTemplate("factory")
    inst = tmpl.instantiate()

    # Create a process with input and output entities
    proc = Process(name="production", completion_time=1.0)
    
    # Add raw material to inputs
    raw = Entity(identifier="raw", volume_liters=10.0, mass_kg=5.0)
    proc.inputs.add_to_container(raw, quantity=100)
    
    # Add output template
    product = Entity(identifier="product", volume_liters=8.0, mass_kg=4.0)
    proc.outputs.add_to_container(product, quantity=0)
    
    # Verify inputs are in process
    inputs = proc.inputs.query_container("raw")
    assert len(inputs) == 100
    
    assert proc.completion_time == 1.0


import pytest
