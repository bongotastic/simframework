import datetime
from pathlib import Path
import sys

try:
    from simframework.system import SystemTemplate, Process, ProcessIO, Store
except ImportError:
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.system import SystemTemplate, Process, ProcessIO, Store


def test_process_io_quantity_per_second():
    """Test ProcessIO rate calculation."""
    # 10 units per hour -> 10/3600 per second
    io = ProcessIO(kind="energy", quantity=10.0, interval=datetime.timedelta(hours=1))
    expected = 10.0 / 3600.0
    assert io.quantity_per_second() == pytest.approx(expected)

    # 60 units per minute -> 1 unit per second
    io2 = ProcessIO(kind="water", quantity=60.0, interval=datetime.timedelta(minutes=1))
    assert io2.quantity_per_second() == pytest.approx(1.0)


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

    p1 = Process(name="production", inputs=[], outputs=[], efficiency=0.9)
    p2 = Process(name="conversion", inputs=[], outputs=[], efficiency=0.8)

    inst.add_process(p1)
    inst.add_process(p2)

    assert len(inst.processes) == 2
    assert inst.processes[0].name == "production"


def test_aggregate_processes_flat():
    """Test aggregating processes from a single system (no children)."""
    tmpl = SystemTemplate("system")
    inst = tmpl.instantiate()

    p1 = Process(name="proc1", efficiency=0.9)
    p2 = Process(name="proc2", efficiency=0.8)

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

    p_parent = Process(name="parent_proc", efficiency=1.0)
    p_child1 = Process(name="child1_proc", efficiency=0.9)
    p_child2 = Process(name="child2_proc", efficiency=0.8)

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


def test_execute_process_success():
    """Test executing a process with sufficient inputs."""
    tmpl = SystemTemplate("factory")
    inst = tmpl.instantiate()

    # Start with 100 units of raw material
    inst.add_store("raw", 100.0)

    # Process: 10 raw per hour -> 8 product per hour (80% efficiency)
    proc = Process(
        name="production",
        inputs=[ProcessIO(kind="raw", quantity=10.0, interval=datetime.timedelta(hours=1))],
        outputs=[ProcessIO(kind="product", quantity=10.0, interval=datetime.timedelta(hours=1))],
        efficiency=0.8,
    )

    # Execute for 1 hour
    duration = datetime.timedelta(hours=1)
    success = inst.execute_process(proc, duration)

    assert success is True
    # After 1 hour: raw should be reduced by 10, product should be added (10 * 0.8 = 8)
    assert inst.get_store("raw").quantity == pytest.approx(90.0)
    assert inst.get_store("product").quantity == pytest.approx(8.0)


def test_execute_process_insufficient_input():
    """Test executing a process with insufficient inputs."""
    tmpl = SystemTemplate("factory")
    inst = tmpl.instantiate()

    # Start with only 5 units but process needs 10
    inst.add_store("raw", 5.0)

    proc = Process(
        name="production",
        inputs=[ProcessIO(kind="raw", quantity=10.0, interval=datetime.timedelta(hours=1))],
        outputs=[ProcessIO(kind="product", quantity=10.0, interval=datetime.timedelta(hours=1))],
        efficiency=0.8,
    )

    duration = datetime.timedelta(hours=1)
    success = inst.execute_process(proc, duration)

    assert success is False
    # Nothing should change
    assert inst.get_store("raw").quantity == pytest.approx(5.0)
    assert inst.get_store("product") is None


def test_execute_process_multiple_inputs_outputs():
    """Test a process with multiple inputs and outputs."""
    tmpl = SystemTemplate("refinery")
    inst = tmpl.instantiate()

    inst.add_store("oil", 100.0)
    inst.add_store("water", 50.0)

    # Refining process: 10 oil + 5 water -> 8 fuel + 2 byproduct (80% efficiency)
    proc = Process(
        name="refining",
        inputs=[
            ProcessIO(kind="oil", quantity=10.0, interval=datetime.timedelta(hours=1)),
            ProcessIO(kind="water", quantity=5.0, interval=datetime.timedelta(hours=1)),
        ],
        outputs=[
            ProcessIO(kind="fuel", quantity=10.0, interval=datetime.timedelta(hours=1)),
            ProcessIO(kind="byproduct", quantity=2.0, interval=datetime.timedelta(hours=1)),
        ],
        efficiency=0.8,
    )

    success = inst.execute_process(proc, datetime.timedelta(hours=1))
    assert success is True

    assert inst.get_store("oil").quantity == pytest.approx(90.0)
    assert inst.get_store("water").quantity == pytest.approx(45.0)
    assert inst.get_store("fuel").quantity == pytest.approx(8.0)  # 10 * 0.8
    assert inst.get_store("byproduct").quantity == pytest.approx(1.6)  # 2 * 0.8


def test_execute_process_fractional_duration():
    """Test executing a process for a fraction of the interval."""
    tmpl = SystemTemplate("factory")
    inst = tmpl.instantiate()

    inst.add_store("raw", 100.0)

    # 60 units per hour (1 per second)
    proc = Process(
        name="production",
        inputs=[ProcessIO(kind="raw", quantity=60.0, interval=datetime.timedelta(hours=1))],
        outputs=[ProcessIO(kind="product", quantity=60.0, interval=datetime.timedelta(hours=1))],
        efficiency=1.0,
    )

    # Execute for 30 minutes (half hour)
    duration = datetime.timedelta(minutes=30)
    success = inst.execute_process(proc, duration)

    assert success is True
    # In 30 minutes, should consume 30 raw and produce 30 product
    assert inst.get_store("raw").quantity == pytest.approx(70.0)
    assert inst.get_store("product").quantity == pytest.approx(30.0)


import pytest
