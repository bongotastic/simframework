"""Unit tests for Scope and Domain classes."""
import pytest

try:
    from simframework.scope import Scope, Domain
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Scope, Domain


class TestScope:
    """Test the Scope class."""

    def test_scope_creation_root(self):
        """Scope without parent should be a root scope."""
        scope = Scope("biology")
        assert scope.name == "biology"
        assert scope.parent is None
        assert scope.full_path() == "biology"

    def test_scope_creation_with_parent(self):
        """Scope with parent should maintain hierarchy."""
        parent = Scope("biology")
        child = Scope("organism", parent=parent)
        assert child.parent is parent
        assert child.full_path() == "biology/organism"

    def test_scope_hierarchy_deep(self):
        """Scope should support deep hierarchies."""
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        growth = Scope("growth", parent=plant)
        assert growth.full_path() == "biology/organism/plant/growth"

    def test_scope_ancestors(self):
        """ancestors() should return all parent scopes."""
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        anc = plant.ancestors()
        assert len(anc) == 2
        assert anc[0] is root
        assert anc[1] is org

    def test_scope_ancestors_root(self):
        """Root scope should have no ancestors."""
        root = Scope("biology")
        assert root.ancestors() == []

    def test_scope_is_ancestor_of(self):
        """is_ancestor_of() should check hierarchy."""
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        assert root.is_ancestor_of(plant)
        assert root.is_ancestor_of(org)
        assert org.is_ancestor_of(plant)
        assert not plant.is_ancestor_of(org)
        assert not org.is_ancestor_of(root)

    def test_scope_depth(self):
        """depth() should return hierarchy level."""
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        assert root.depth() == 0
        assert org.depth() == 1
        assert plant.depth() == 2

    def test_scope_properties(self):
        """Scope should store custom properties."""
        scope = Scope("growth", properties={"color": "green", "speed": 1.5})
        assert scope.properties["color"] == "green"
        assert scope.properties["speed"] == 1.5

    def test_scope_equality(self):
        """Scopes with same full path should be equal."""
        root1 = Scope("biology")
        org1 = Scope("organism", parent=root1)
        root2 = Scope("biology")
        org2 = Scope("organism", parent=root2)
        assert org1 == org2

    def test_scope_hash(self):
        """Scopes should be hashable for use in sets/dicts."""
        root = Scope("biology")
        org = Scope("organism", parent=root)
        scope_set = {org, org}
        assert len(scope_set) == 1

    def test_scope_repr(self):
        """Scope should have meaningful repr."""
        root = Scope("biology")
        org = Scope("organism", parent=root, properties={"type": "living"})
        repr_str = repr(org)
        assert "biology/organism" in repr_str
        assert "type" in repr_str


class TestDomain:
    """Test the Domain class."""

    def test_domain_creation(self):
        """Domain should be creatable with a name."""
        domain = Domain("EcologicalSim")
        assert domain.name == "EcologicalSim"
        assert domain.list_all_scopes() == []

    def test_domain_register_scope(self):
        """Domain should register scopes."""
        domain = Domain("EcologicalSim")
        scope = Scope("biology")
        domain.register_scope(scope)
        assert len(domain.list_all_scopes()) == 1

    def test_domain_register_scope_hierarchy(self):
        """Domain should register scope hierarchies."""
        domain = Domain("EcologicalSim")
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        domain.register_scope(root)
        domain.register_scope(org)
        domain.register_scope(plant)
        assert len(domain.list_all_scopes()) == 3

    def test_domain_register_duplicate_scope(self):
        """Domain should reject duplicate scope paths."""
        domain = Domain("EcologicalSim")
        root1 = Scope("biology")
        root2 = Scope("biology")
        domain.register_scope(root1)
        with pytest.raises(ValueError):
            domain.register_scope(root2)

    def test_domain_get_scope(self):
        """Domain should retrieve scopes by full path."""
        domain = Domain("EcologicalSim")
        root = Scope("biology")
        org = Scope("organism", parent=root)
        domain.register_scope(root)
        domain.register_scope(org)
        retrieved = domain.get_scope("biology/organism")
        assert retrieved is org

    def test_domain_get_scope_not_found(self):
        """Domain should return None for non-existent scope."""
        domain = Domain("EcologicalSim")
        assert domain.get_scope("nonexistent/path") is None

    def test_domain_get_scopes_by_ancestor(self):
        """Domain should filter scopes by ancestor."""
        domain = Domain("EcologicalSim")
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        animal = Scope("animal", parent=org)
        domain.register_scope(root)
        domain.register_scope(org)
        domain.register_scope(plant)
        domain.register_scope(animal)
        
        # Get all scopes under "organism"
        org_scopes = domain.get_scopes_by_ancestor(org)
        assert org in org_scopes
        assert plant in org_scopes
        assert animal in org_scopes
        assert root not in org_scopes

    def test_domain_scopes_at_depth(self):
        """Domain should filter scopes by depth."""
        domain = Domain("EcologicalSim")
        root = Scope("biology")
        org = Scope("organism", parent=root)
        plant = Scope("plant", parent=org)
        domain.register_scope(root)
        domain.register_scope(org)
        domain.register_scope(plant)
        
        depth0 = domain.scopes_at_depth(0)
        depth1 = domain.scopes_at_depth(1)
        depth2 = domain.scopes_at_depth(2)
        
        assert root in depth0
        assert org in depth1
        assert plant in depth2

    def test_domain_repr(self):
        """Domain should have meaningful repr."""
        domain = Domain("EcologicalSim")
        root = Scope("biology")
        domain.register_scope(root)
        repr_str = repr(domain)
        assert "EcologicalSim" in repr_str
        assert "scopes=1" in repr_str


class TestScopeIntegration:
    """Test Scope and Domain integration."""

    def test_build_domain_tree(self):
        """Should be able to build a complete domain taxonomy."""
        domain = Domain("EcologicalSim")
        
        # Build hierarchy
        biology = Scope("biology")
        organism = Scope("organism", parent=biology)
        plant = Scope("plant", parent=organism)
        animal = Scope("animal", parent=organism)
        growth = Scope("growth", parent=plant)
        reproduction = Scope("reproduction", parent=animal)
        
        for scope in [biology, organism, plant, animal, growth, reproduction]:
            domain.register_scope(scope)
        
        # Verify structure
        assert len(domain.list_all_scopes()) == 6
        assert domain.get_scope("biology/organism/plant/growth") is growth
        assert domain.get_scope("biology/organism/animal/reproduction") is reproduction
        
        # Verify filtering
        plant_scopes = domain.get_scopes_by_ancestor(plant)
        assert plant in plant_scopes
        assert growth in plant_scopes
        assert reproduction not in plant_scopes

    def test_scope_with_domain_metadata(self):
        """Scopes should support domain-specific metadata."""
        domain = Domain("WeatherSim")
        
        weather = Scope("weather", properties={"system": "meteorological"})
        rain = Scope("rain", parent=weather, properties={"intensity_range": (0, 100)})
        
        domain.register_scope(weather)
        domain.register_scope(rain)
        
        retrieved_rain = domain.get_scope("weather/rain")
        assert retrieved_rain.properties["intensity_range"] == (0, 100)
