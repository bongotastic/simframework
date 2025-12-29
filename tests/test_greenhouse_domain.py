from pathlib import Path

try:
    from simframework.scope import Domain
    from simframework.system import SystemTemplate
except ImportError:
    import sys
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain
    from simframework.system import SystemTemplate


def test_greenhouse_domain_loads():
    p = Path(__file__).resolve().parents[1] / "simulations" / "GreenHouse" / "domain.yaml"
    d = Domain.from_yaml(str(p))
    assert d.name == "GreenHouseDomain"
    # scope exists and child scopes exist
    assert d.get_scope("environment") is not None
    assert d.get_scope("environment/temperature") is not None
    assert d.get_scope("environment/temperature/heat_loss") is not None
    assert d.get_scope("environment/light") is not None
    assert d.get_scope("environment/moisture") is not None
    # system template exists and contains environmental properties
    assert "Greenhouse" in d.system_templates
    mt = d.get_system_template("Greenhouse")
    assert mt is not None
    assert mt.property_spec("temperature") is not None
    assert mt.property_spec("temperature").default == 22.0
    assert mt.property_spec("moisture") is not None
    assert mt.property_spec("moisture").default == 0.35
    assert mt.property_spec("light") is not None
    assert mt.property_spec("light").default == 12000

    # Sub-systems are modeled as child templates attached to the Greenhouse
    child_names = [c.name for c in mt.children]
    assert "Chamber" in child_names
    assert "PowerUnit" in child_names

    # Validate Chamber properties
    chamber_t = next(c for c in mt.children if c.name == "Chamber")
    assert chamber_t.property_spec("volume") is not None
    assert chamber_t.property_spec("volume").default == 100.0
    assert chamber_t.property_spec("volume").metadata.get("unit") == "m^3"

    # Validate PowerUnit and its Heater child
    power_t = next(c for c in mt.children if c.name == "PowerUnit")
    assert power_t.property_spec("max_capacity") is not None
    assert power_t.property_spec("max_capacity").default == 5000
    assert any(c.name == "Heater" for c in power_t.children)

    heater_t = next(c for c in power_t.children if c.name == "Heater")
    assert heater_t.property_spec("input_w") is not None
    assert heater_t.property_spec("output_w") is not None
    assert heater_t.property_spec("input_w").default == 1000
    assert heater_t.property_spec("output_w").default == 900

    assert d.get_agent_template("Greenhouse") is None
