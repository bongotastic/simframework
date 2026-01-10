from simulations.Demesne.DemesneSimulation import DemesneSimulation


def test_demesne_simulation_has_calendar():
    sim = DemesneSimulation()
    assert hasattr(sim, "calendar")
    # calendar should have loaded entries from the YAML
    assert len(sim.calendar.entries) > 0


def test_demesne_simulation_reuses_calendar_when_provided():
    base = DemesneSimulation()
    # create a new sim using existing engine, should reuse calendar instance
    sim2 = DemesneSimulation(engine=base)
    assert sim2.calendar is base.calendar
