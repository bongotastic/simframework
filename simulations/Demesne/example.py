"""Minimal example entrypoint for the Demesne simulation (stub).

This example is intentionally minimal: it demonstrates importing the
simulation class and setting an inception time without requiring an
engine or other infrastructure. The full demo in the repository may
depend on a configured engine and domain which are not created here.
"""

from datetime import datetime
from simulations.Demesne.DemesneSimulation import DemesneSimulation


def main():
    sim = DemesneSimulation()

    # set inception time to July 6, 770 AD (demonstration only)
    sim.inception_time = datetime(770, 7, 6)

    landplot = sim.create_landplot(
        identifier="demo-plot",
        stage_path="land/cultivated/crop/growing/early",
        vegetation_path="source/plant/species/cereal/wheat",
        acreage=5.0,
    )
    
    sim.run()


if __name__ == "__main__":
    main()
