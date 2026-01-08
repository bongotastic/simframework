import pytest

from simframework.engine import SimulationEngine
from simframework.scope import Scope, Domain


def test_ensure_scope_creates_hierarchy_when_domain_missing():
    eng = SimulationEngine()
    # Force domain to None to test lazy creation
    eng.domain = None

    scope = eng.ensure_scope("aa/bb/cc")

    assert scope is not None
    assert scope.full_path() == "aa/bb/cc"
    assert eng.domain is not None
    assert eng.domain.get_scope("aa") is not None
    assert eng.domain.get_scope("aa/bb") is not None
    assert eng.domain.get_scope("aa/bb/cc") is scope
    assert scope.parent.name == "bb"
    assert scope.parent.parent.name == "aa"


def test_ensure_scope_uses_existing_ancestors():
    eng = SimulationEngine()
    # create a domain and register a single ancestor
    eng.domain = Domain("testdomain")
    root = Scope(name="aa")
    eng.domain.register_scope(root)

    scope = eng.ensure_scope("aa/bb/cc")

    assert eng.domain.get_scope("aa") is root
    assert eng.domain.get_scope("aa/bb") is not None
    assert scope.parent.parent is root


def test_ensure_scope_returns_existing_scope_if_present():
    eng = SimulationEngine()
    eng.domain = Domain("testdomain")
    # Register whole path ahead of time
    s1 = Scope(name="aa")
    eng.domain.register_scope(s1)
    s2 = Scope(name="bb", parent=s1)
    eng.domain.register_scope(s2)
    s3 = Scope(name="cc", parent=s2)
    eng.domain.register_scope(s3)

    result = eng.ensure_scope("aa/bb/cc")
    assert result is s3
