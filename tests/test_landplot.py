import pytest

from simframework.scope import Domain
from simulations.Demesne.landplot import LandPlot


def test_landplot_basic_creation():
    d = Domain.from_yaml("simulations/Demesne")

    # use existing scope paths from the Demesne domain
    stage_path = "plant/crop/cereal/wheat"
    veg_path = "plant/crop/cereal/wheat"

    stage_scope = d.get_scope(stage_path)
    veg_scope = d.get_scope(veg_path)

    lp = LandPlot(identifier="plot-1", stage=stage_scope, vegetation=veg_scope, acreage=2.5)

    assert lp.identifier == "plot-1"
    assert lp.acreage == 2.5
    assert lp.stage is stage_scope
    assert lp.vegetation is veg_scope


def test_landplot_setters_and_validation():
    d = Domain.from_yaml("simulations/Demesne")
    lp = LandPlot(identifier="plot-2", acreage=1.0)

    # invalid acreage
    with pytest.raises(ValueError):
        LandPlot(identifier="bad", acreage=-1)

    # set stage/vegetation via setters
    stage = d.get_scope("plant/crop/cereal/wheat")
    veg = d.get_scope("plant/crop/cereal/wheat/grain")
    lp.set_stage(stage)
    lp.set_vegetation(veg)
    assert lp.stage is stage
    assert lp.vegetation is veg
