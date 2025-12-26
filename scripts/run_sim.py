"""Simple demo runner for the simulation framework."""
from simframework import SimulationEngine

class Printer:
    def __init__(self, name):
        self.name = name
    def __call__(self, message):
        print(message)


def main():
    engine = SimulationEngine()
    engine.schedule(0, lambda: print(f"Start at t={engine.scheduler.now}"))
    engine.schedule(1.5, lambda: print(f"Event at t={engine.scheduler.now}: hello"))
    engine.schedule(0.5, lambda: print(f"Event at t={engine.scheduler.now}: quick"))
    engine.run()

if __name__ == "__main__":
    main()
