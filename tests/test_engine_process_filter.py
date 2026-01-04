from simframework.engine import SimulationEngine


def test_get_process_including_filters():
    engine = SimulationEngine()

    # Input-only filter (seed_stock -> sowing)
    procs = engine.get_process_including(input="item/organic/plant/seed_stock")
    assert any(p.path == "process/cultivation/sowing" for p in procs)

    # Output-only filter (seeded -> sowing)
    procs = engine.get_process_including(output="land/cultivated/crop/seeded")
    assert any(p.path == "process/cultivation/sowing" for p in procs)

    # Both input and output
    procs = engine.get_process_including(input="item/organic/plant/seed_stock", output="land/cultivated/crop/seeded")
    assert len(procs) == 1
    assert procs[0].path == "process/cultivation/sowing"

    # Sheaf -> threshing produces grain
    procs = engine.get_process_including(input="item/organic/plant/sheaf", output="item/organic/plant/grain")
    assert any(p.path == "process/processing/threshing" for p in procs)

    # No filters -> all processes
    all_procs = engine.get_process_including()
    assert len(all_procs) == len(engine.processes)
