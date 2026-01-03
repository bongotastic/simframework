"""Run a tiny Generic simulation demo (loads domain and prints scopes)."""
from pathlib import Path
from simframework.scope import Domain


def main():
    pkg_root = Path(__file__).resolve().parents[1]
    yaml_file = pkg_root / "simulations" / "Generic" / "domain.yaml"
    domain = Domain.from_yaml(str(yaml_file))
    print("Loaded domain:", domain.name)
    for s in domain.scopes_at_depth(0):
        print("-", s.name)


if __name__ == "__main__":
    main()
