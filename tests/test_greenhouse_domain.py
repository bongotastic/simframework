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
    assert d.get_scope("environment/light") is not None
    assert d.get_scope("environment/moisture") is not None
    # system template exists
    assert "Greenhouse" in d.system_templates
    assert d.get_agent_template("Greenhouse") is None
