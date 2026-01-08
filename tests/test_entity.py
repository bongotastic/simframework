import pytest
from simframework.entity import Entity


def test_entity_creation():
    """Test creating an entity with valid parameters."""
    entity = Entity(identifier="environment/temperature/sensor", volume_liters=2.5, mass_kg=1.2)
    assert entity.identifier == "environment/temperature/sensor"
    assert entity.volume_liters == pytest.approx(2.5)
    assert entity.mass_kg == pytest.approx(1.2)


def test_entity_defaults():
    """Test entity creation with default values."""
    entity = Entity(identifier="tool/hammer")
    assert entity.identifier == "tool/hammer"
    assert entity.volume_liters == pytest.approx(0.0)  # Default volume
    assert entity.mass_kg == pytest.approx(0.0)  # Default mass
    # No reliability/ablative fields; defaults checked above


# reliability/ablative removed: no tests for them


def test_volume_and_mass_validation():
    """Test volume_liters and mass_kg must be non-negative numbers."""
    # Valid bounds
    Entity(identifier="test", volume_liters=0.0)
    Entity(identifier="test", volume_liters=2.5)
    Entity(identifier="test", mass_kg=0.0)
    Entity(identifier="test", mass_kg=2.5)

    # Invalid volume: negative
    with pytest.raises(ValueError, match="volume_liters must be a non-negative number"):
        Entity(identifier="test", volume_liters=-0.1)

    # Invalid mass: negative
    with pytest.raises(ValueError, match="mass_kg must be a non-negative number"):
        Entity(identifier="test", mass_kg=-0.1)


def test_container_add_query_and_remove():
    """Test adding, querying, and removing entities from a container."""
    parent = Entity(identifier="box")
    
    # Create 3 individual knife entities
    knife1 = Entity(identifier="knife", volume_liters=0.02, mass_kg=0.1)
    knife2 = Entity(identifier="knife", volume_liters=0.02, mass_kg=0.1)
    knife3 = Entity(identifier="knife", volume_liters=0.02, mass_kg=0.1)
    
    parent.add_to_container([knife1, knife2, knife3])

    # Query
    found = parent.query_container("knife")
    assert len(found) == 3
    assert all(e.identifier == "knife" for e in found)

    # Remove 2 entities
    removed = parent.remove_from_container("knife", count=2)
    assert len(removed) == 2

    # Remaining in parent should be 1
    remaining = parent.query_container("knife")
    assert len(remaining) == 1


def test_container_remove_all():
    """Test removing all entities from a container."""
    parent = Entity(identifier="crate")
    ent1 = Entity(identifier="item")
    ent2 = Entity(identifier="item")
    
    parent.add_to_container([ent1, ent2])
    
    # Remove all
    removed = parent.remove_from_container("item", count=10)
    assert len(removed) == 2
    
    # Container should be empty
    remaining = parent.query_container("item")
    assert len(remaining) == 0


def test_container_add_with_quantity():
    """Test adding a single entity multiple times using quantity parameter."""
    parent = Entity(identifier="crate")
    nail = Entity(identifier="nail", volume_liters=0.001, mass_kg=0.01)
    
    # Add 1000 copies of the nail
    parent.add_to_container(nail, quantity=1000)
    
    # Query should return 1000 individual nail entities
    found = parent.query_container("nail")
    assert len(found) == 1000
    assert all(e.identifier == "nail" for e in found)
    assert all(e.volume_liters == pytest.approx(0.001) for e in found)
    
    # Remove 500
    removed = parent.remove_from_container("nail", count=500)
    assert len(removed) == 500
    
    # Should have 500 remaining
    remaining = parent.query_container("nail")
    assert len(remaining) == 500


def test_ablate():
    """Test ablating an entity's ablative value (ablate method)."""
    # ablate() was removed; ensure calling it raises AttributeError
    entity = Entity(identifier="tool")
    with pytest.raises(AttributeError):
        entity.ablate(0.3)


def test_reliability_test(monkeypatch):
    """Test deterministic reliability_test behavior via monkeypatching random.randint."""
    # reliability_test() was removed; calling it should raise AttributeError
    e = Entity(identifier="test")
    with pytest.raises(AttributeError):
        e.reliability_test()

