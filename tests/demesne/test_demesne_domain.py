from pathlib import Path

try:
    from simframework.scope import Domain
except ImportError:
    import sys
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain


def test_demesne_domain_exists():
    """Ensure the Demesne domain stub exists and loads."""
    p = Path(__file__).resolve().parents[1] / "simulations" / "Demesne" / "domain.yaml"
    d = Domain.from_yaml(str(p))
    assert d.name == "Demesne"
    # No scopes or systems defined in stub
    assert d.get_scope("environment") is None
    assert d.system_templates == {}
