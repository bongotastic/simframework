"""Example entrypoint for the Demesne simulation (stub)."""
from .simulation import DemesneSimulation


def main():
    sim = DemesneSimulation()
    sim.setup()
    sim.run()


if __name__ == "__main__":
    main()
