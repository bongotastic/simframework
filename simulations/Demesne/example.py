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

    # Create a location (demonstration only)
    my_location = sim.create_location(
        identifier="demo-location",
        essence="land/plot/arable"
    )
    my_location.traversal_meter = 500.0  # set traversal meters (demonstration only)

    # create a sample landplot (demonstration only)
    landplot = sim.create_landplot(
        identifier="demo-plot",
        essence= sim.domain.get_scope("land/plot/arable"),
        stage_path= sim.domain.get_scope("state/growth/vegetative"),
        vegetation_path= sim.domain.get_scope("source/plant/species/cereal/wheat"),
        acreage=2.0,
    )

    # Add the plot to the location (demonstration only)
    my_location.add_content(landplot)
    
    sim.run()


if __name__ == "__main__":
    main()
