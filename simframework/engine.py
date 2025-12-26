"""Minimal simulation engine coordinating entities and the scheduler."""
from typing import List
from .scheduler import Scheduler
from .entity import Entity

class SimulationEngine:
    def __init__(self, start_time: float = 0.0):
        self.scheduler = Scheduler(start_time=start_time)
        self.entities: List[Entity] = []

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)

    def schedule(self, delay: float, callback, *args, **kwargs):
        return self.scheduler.schedule(delay, callback, *args, **kwargs)

    def run(self, until: float = None) -> None:
        self.scheduler.run(until=until)
