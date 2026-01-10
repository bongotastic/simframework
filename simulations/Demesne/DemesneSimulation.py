"""Demesne simulation stub."""

from typing import Optional
from datetime import datetime
from simframework.engine import SimulationEngine

from simframework.entity import Entity
from simframework.scope import Scope
from simulations.Demesne.landplot import LandPlot
from simulations.Demesne.calendar import Calendar


class DemesneSimulation(SimulationEngine):
    def __init__(self, engine: Optional[SimulationEngine] = None, start_time: Optional[datetime] = None):
        """DemesneSimulation is a SimulationEngine specialized for the Demesne demo.

        If `engine` is provided the new instance will reuse its core attributes
        (scheduler, registries, domain/process lists). Otherwise a fresh
        `SimulationEngine` instance is initialized via `super()`.
        """
        if engine is None:
            super().__init__(start_time=start_time)
            # Load the Demesne calendar for this simulation
            self.calendar = Calendar()
        else:
            # Shallow copy key runtime attributes from provided engine
            self.scheduler = engine.scheduler
            self.default_beta = getattr(engine, "default_beta", 10.0)
            self.entities = getattr(engine, "entities", {})
            self._entity_counter = getattr(engine, "_entity_counter", 0)
            self.inception_time = getattr(engine, "inception_time", self.scheduler.now)
            self.domain = getattr(engine, "domain", None)
            self.processes = getattr(engine, "processes", {})
            # Reuse calendar from provided engine if present, otherwise load a new one
            self.calendar = getattr(engine, "calendar", Calendar())

    def setup(self):
        """Set up domain and systems (stub)."""

        # Placeholder for end of simulation as an event.
        end_simulation_time = 365 * 24.0  # 1 year in hours
        # Schedule using this engine's scheduler
        end_event = self.scheduler.schedule(end_simulation_time, message="End Simulation")

    def create_persons(self):
        """Create person agents (stub)."""
        pass

    def create_landplot(self, identifier: Optional[str] = None, *, essence: Optional[Scope] = None, stage_path: Optional[str] = None, vegetation_path: Optional[str] = None, acreage: float = 1.0) -> LandPlot:
        """Create a `LandPlot` instance resolved against this engine's `domain`.

        Args:
            identifier: optional identifier for the LandPlot; if omitted, a unique id is generated.
            stage_path: optional scope full path for the growth stage.
            vegetation_path: optional scope full path for the vegetation.
            acreage: plot area in acres.

        Returns:
            LandPlot instance.
        """
        # Use the engine's domain to resolve stage/vegetation scopes when available
        dom = self.domain

        # resolve scopes for stage and vegetation
        stage = self.domain.get_scope(stage_path) if (dom is not None and stage_path) else None
        veg = self.domain.get_scope(vegetation_path) if (dom is not None and vegetation_path) else None

        # Generate an identifier if none provided
        if identifier is None:
            identifier = f"landplot_{self._entity_counter}"
            self._entity_counter += 1

        # instantiate LandPlot and register to the simulation
        lp = LandPlot(identifier=identifier, stage=stage, vegetation=veg, acreage=acreage)
        self.add_entity(lp)

        return lp
    
    def create_location(self, identifier: str, essence: Optional[Scope] = None):
        """Create a location entity (stub)."""
        unique_id = self.NewUniqueIdentifier(identifier)

        if type(essence) == str:
            essence = self.domain.get_scope(essence)
        
        location = Entity(essence=essence, identifier=unique_id)
        self.add_entity(location)
        
        return location
        



    def run(self):
        """Run the simulation (stub)."""

        # Last event was a heartbeat; continue processing events
        last_was_heartbeat = False

        while True:
            # Fetch next event
            event = self.step()
            if event is None:
                break

            # get scope of event
            this_scope = event.scope.full_path() if event.scope else "N/A"

            # Prevent infinite loop on heartbeat events
            if this_scope == "heartbeat" and len(self.scheduler._queue) == 1 and last_was_heartbeat:
                break

            # Dispatch 
            if this_scope == "heartbeat":
                self.handle_heartbeat(event)
                last_was_heartbeat = True
            elif this_scope.startswith("process/crop"):
                self.handle_crop_evolution(event)
                last_was_heartbeat = False
            else:
                # For other events, just print for now
                self.log(f"Processing event for unknown scope '{this_scope}' with data: {event.data}") 
                last_was_heartbeat = False
 

    def handle_heartbeat(self, event):
        """Handle heartbeat events (stub)."""
        # For demonstration, just print heartbeat occurrence
        self.log(f"Heartbeat")

    def handle_crop_evolution(self, event):
        """Handle crop evolution events (stub)."""
        # For demonstration, just print crop evolution occurrence
        self.log(f"Crop evolution event for {event.entity_anchor.name} with process: {event.scope.full_path()}")