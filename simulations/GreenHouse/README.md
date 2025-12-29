# GreenHouse Demo

This folder contains a minimal demonstration of the GreenHouse domain
and a convenience simulation wrapper.

Files
- `domain.yaml` — YAML domain describing scopes and the `Greenhouse` system template.
- `simulation.py` — `GreenhouseSimulation` class (inherits from `SimulationEngine`) with:
  - `setup_greenhouse()` — instantiate and register a greenhouse system
  - `schedule_environment_events()` — schedule sample environment events (temperature, moisture, light)
  - `dispatch_event()` — simple routing to handlers
  - `run_and_dispatch()` — convenience loop to process and handle events
  - Simple handlers: `on_temperature_event`, `on_moisture_event`, `on_light_event`
- `example.py` — runnable demo script that sets up the greenhouse, schedules events, and runs the dispatch loop
- `test_simulation.py` — pytest tests covering instantiation, scheduling, and dispatch behavior

Running the demo

From the project root, run:

    PYTHONPATH=. python simulations/GreenHouse/example.py

This prints initial and final greenhouse properties and demonstrates how the
handlers change the greenhouse state.

Running tests

Run the GreenHouse test directly:

    PYTHONPATH=. python -m pytest simulations/GreenHouse/test_simulation.py

CI

The repository CI includes steps to run the GreenHouse example and tests (see `.github/workflows/python.yml`).

Extending the demo

Replace or extend the handler methods in `GreenhouseSimulation` to add actuators,
periodic scheduling, agents, or more realistic environment models.
