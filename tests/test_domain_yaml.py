from pathlib import Path

try:
    from simframework.scope import Domain
except ImportError:
    import sys
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain


def test_domain_from_yaml_lunarstation():
    pkg_root = Path(__file__).resolve().parents[1]
    yaml_file = pkg_root / "simulations" / "LunarStation" / "domain.yaml"
    assert yaml_file.exists(), f"Expected domain YAML at {yaml_file}"

    domain = Domain.from_yaml(str(yaml_file))
    assert domain.name == "LunarStationDomain"

    top = {s.name for s in domain.scopes_at_depth(0)}
    assert {"weather", "communication", "personnel"}.issubset(top)

    sf = domain.get_scope("weather/radiation/solar_flare")
    assert sf is not None
    assert sf.properties.get("severity") == "high"

    suit = domain.get_scope("personnel/eva/suit_breach")
    assert suit is not None
    assert suit.properties.get("severity") == "critical"
