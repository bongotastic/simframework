from pathlib import Path
import tempfile
import os

try:
    from simframework.scope import Domain
except ImportError:
    import sys
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain


def test_from_yaml_missing_path_raises():
    missing = "simulations/does_not_exist/domain.yaml"
    try:
        Domain.from_yaml(missing)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_from_yaml_directory_loading(tmp_path):
    # Create two small YAML files to simulate modular domain pieces
    file1 = tmp_path / "part1.yaml"
    file1.write_text("""
name: TestDirDomain
scopes:
  - path: root/a
    properties:
      x: 1
  - path: root/b
    properties:
      y: 2
""")

    file2 = tmp_path / "part2.yaml"
    file2.write_text("""
scopes:
  - path: root/c
    properties:
      z: 3
  - path: other/d
    properties:
      w: 4
""")

    domain = Domain.from_yaml(str(tmp_path))
    assert domain.name == "TestDirDomain"
    assert domain.get_scope("root/a") is not None
    assert domain.get_scope("root/c").properties.get("z") == 3
    assert domain.get_scope("other/d").properties.get("w") == 4


def test_from_yaml_empty_scopes_returns_domain(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("name: EmptyDomain\n")
    domain = Domain.from_yaml(str(f))
    assert domain.name == "EmptyDomain"
    assert domain.list_all_scopes() == []
