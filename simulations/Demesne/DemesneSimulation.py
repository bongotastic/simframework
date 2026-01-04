"""Demesne simulation stub."""

from typing import Optional
from datetime import datetime
from simframework.engine import SimulationEngine

from simulations.Demesne.landplot import LandPlot


class DemesneSimulation(SimulationEngine):
    def __init__(self, engine: Optional[SimulationEngine] = None, start_time: Optional[datetime] = None):
        """DemesneSimulation is a SimulationEngine specialized for the Demesne demo.

        If `engine` is provided the new instance will reuse its core attributes
        (scheduler, registries, domain/process lists). Otherwise a fresh
        `SimulationEngine` instance is initialized via `super()`.
        """
        if engine is None:
            super().__init__(start_time=start_time)
        else:
            # Shallow copy key runtime attributes from provided engine
            self.scheduler = engine.scheduler
            self.default_beta = getattr(engine, "default_beta", 10.0)
            self.entities = getattr(engine, "entities", {})
            self._entity_counter = getattr(engine, "_entity_counter", 0)
            self.inception_time = getattr(engine, "inception_time", self.scheduler.now)
            self.domain = getattr(engine, "domain", None)
            self.processes = getattr(engine, "processes", {})

    def setup(self):
        """Set up domain and systems (stub)."""

        # Placeholder for end of simulation as an event.
        end_simulation_time = 365 * 24.0  # 1 year in hours
        # Schedule using this engine's scheduler
        end_event = self.scheduler.schedule(end_simulation_time, message="End Simulation")

    def create_persons(self):
        """Create person agents (stub)."""
        pass

    def create_landplot(self, identifier: Optional[str] = None, domain: Optional[object] = None, *, stage_path: Optional[str] = None, vegetation_path: Optional[str] = None, acreage: float = 1.0) -> LandPlot:
        """Create a `LandPlot` instance resolved against `domain` (default: engine domain).

        Args:
            identifier: optional identifier for the LandPlot; if omitted, a unique id is generated.
            domain: optional `Domain` instance used to resolve `stage_path` and `vegetation_path` (defaults to engine domain).
            stage_path: optional scope full path for the growth stage.
            vegetation_path: optional scope full path for the vegetation.
            acreage: plot area in acres.

        Returns:
            LandPlot instance.
        """
        # Use provided domain or fall back to this engine's domain
        dom = domain if domain is not None else getattr(self, "domain", None)

        stage = None
        veg = None
        if dom is not None:
            if stage_path:
                try:
                    stage = dom.get_scope(stage_path)
                except Exception:
                    stage = None
            if vegetation_path:
                try:
                    veg = dom.get_scope(vegetation_path)
                except Exception:
                    veg = None

        # Generate an identifier if none provided
        if identifier is None:
            identifier = f"landplot_{self._entity_counter}"
            self._entity_counter += 1

        lp = LandPlot(identifier=identifier, stage=stage, vegetation=veg, acreage=acreage)
        return lp

    def run(self):
        """Run the simulation (stub)."""
        pass
