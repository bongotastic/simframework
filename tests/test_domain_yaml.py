from pathlib import Path

try:
    from simframework.scope import Domain
except ImportError:
    import sys
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain


def test_domain_from_yaml_demesne():
    pkg_root = Path(__file__).resolve().parents[1]
    yaml_file = pkg_root / "simulations" / "Demesne" / "domain.yaml"
    assert yaml_file.exists(), f"Expected domain YAML at {yaml_file}"

    domain = Domain.from_yaml(str(yaml_file))
    assert domain.name == "Demesne"

    # Domain should include top-level 'land' and 'goods' scopes
    assert domain.get_scope("land") is not None
    assert domain.get_scope("goods/tools/agriculture/sickle") is not None

    top_level_names = {s.name for s in domain.scopes_at_depth(0)}
    assert "land" in top_level_names
    assert "goods" in top_level_names
