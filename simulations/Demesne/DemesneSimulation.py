"""Demesne simulation stub."""

from typing import Optional
from datetime import datetime

from simulations.Demesne.landplot import LandPlot


class DemesneSimulation:
    def __init__(self, engine=None):
        self.engine = engine
        # store inception as a datetime; use imported `datetime` class
        self.inception_time = datetime.now()

    def setup(self):
        """Set up domain and systems (stub)."""

        # Placeholder for end of simulation as an event.
        end_simulation_time = 365 * 24.0  # 1 year in hours
        end_event = self.engine.scheduler.schedule(
            end_simulation_time, message="End Simulation"
        )

    def create_persons(self):
        """Create person agents (stub)."""
        pass

    def create_landplot(self, identifier: str, domain: Optional[object] = None, *, stage_path: Optional[str] = None, vegetation_path: Optional[str] = None, acreage: float = 1.0) -> LandPlot:
        """Create a `LandPlot` instance resolved against `domain` (if provided).

        Args:
            identifier: identifier for the LandPlot (passed to `Entity.identifier`).
            domain: optional `Domain` instance used to resolve `stage_path` and `vegetation_path`.
            stage_path: optional scope full path for the growth stage.
            vegetation_path: optional scope full path for the vegetation.
            acreage: plot area in acres.

        Returns:
            LandPlot instance.
        """
        stage = None
        veg = None
        if domain is not None:
            if stage_path:
                try:
                    stage = domain.get_scope(stage_path)
                except Exception:
                    stage = None
            if vegetation_path:
                try:
                    veg = domain.get_scope(vegetation_path)
                except Exception:
                    veg = None

        lp = LandPlot(identifier=identifier, stage=stage, vegetation=veg, acreage=acreage)
        return lp

    def run(self):
        """Run the simulation (stub)."""
        pass
