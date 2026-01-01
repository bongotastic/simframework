import pytest
from simframework.entity import Entity


def test_entity_creation():
    """Test creating an entity with valid parameters."""
    entity = Entity(identifier="environment/temperature/sensor", reliability=8.5, ablative=0.1)
    assert entity.identifier == "environment/temperature/sensor"
    assert entity.reliability == pytest.approx(8.5)
    assert entity.ablative == pytest.approx(0.1)


def test_entity_defaults():
    """Test entity creation with default values."""
    entity = Entity(identifier="tool/hammer")
    assert entity.identifier == "tool/hammer"
    assert entity.reliability == pytest.approx(10.0)  # Default: fully reliable
    assert entity.ablative == pytest.approx(0.0)  # Default: no degradation


def test_entity_reliability_validation():
    """Test that reliability is validated to be within [0, 10]."""
    # Valid bounds
    Entity(identifier="test", reliability=0.0)
    Entity(identifier="test", reliability=10.0)
    Entity(identifier="test", reliability=5.0)

    # Invalid: too high
    with pytest.raises(ValueError, match="reliability must be between 0 and 10"):
        Entity(identifier="test", reliability=10.1)

    # Invalid: too low
    with pytest.raises(ValueError, match="reliability must be between 0 and 10"):
        Entity(identifier="test", reliability=-0.1)


def test_entity_ablative_validation():
    """Test that ablative is validated to be within [0, 1]."""
    # Valid bounds
    Entity(identifier="test", ablative=0.0)
    Entity(identifier="test", ablative=1.0)
    Entity(identifier="test", ablative=0.5)

    # Invalid: too high
    with pytest.raises(ValueError, match="ablative must be between 0 and 1"):
        Entity(identifier="test", ablative=1.1)

    # Invalid: too low
    with pytest.raises(ValueError, match="ablative must be between 0 and 1"):
        Entity(identifier="test", ablative=-0.01)


def test_degrade():
    """Test degrading an entity's ablative value."""
    entity = Entity(identifier="tool", ablative=0.2)

    # Degrade by 0.3
    entity.degrade(0.3)
    assert entity.ablative == pytest.approx(0.5)

    # Degrade past the limit (should clamp to 1.0)
    entity.degrade(0.6)
    assert entity.ablative == pytest.approx(1.0)


def test_repair():
    """Test repairing an entity's ablative value."""
    entity = Entity(identifier="tool", ablative=0.8)

    # Repair by 0.2
    entity.repair(0.2)
    assert entity.ablative == pytest.approx(0.6)

    # Repair past the limit (should clamp to 0.0)
    entity.repair(0.7)
    assert entity.ablative == pytest.approx(0.0)


def test_set_reliability():
    """Test setting reliability with clamping."""
    entity = Entity(identifier="sensor", reliability=8.0)

    # Set valid value
    entity.set_reliability(7.0)
    assert entity.reliability == pytest.approx(7.0)

    # Set above limit (should clamp)
    entity.set_reliability(12.0)
    assert entity.reliability == pytest.approx(10.0)

    # Set below limit (should clamp)
    entity.set_reliability(-1.0)
    assert entity.reliability == pytest.approx(0.0)


def test_is_functional():
    """Test the is_functional method."""
    # Fully functional
    entity = Entity(identifier="test", reliability=10.0, ablative=0.0)
    assert entity.is_functional() is True

    # Reliability is zero (not functional)
    entity = Entity(identifier="test", reliability=0.0, ablative=0.0)
    assert entity.is_functional() is False

    # Fully ablated (not functional)
    entity = Entity(identifier="test", reliability=10.0, ablative=1.0)
    assert entity.is_functional() is False

    # Partially degraded (still functional)
    entity = Entity(identifier="test", reliability=5.0, ablative=0.5)
    assert entity.is_functional() is True


def test_effectiveness():
    """Test effectiveness calculation."""
    # Fully effective: 10 reliability, 0 ablative -> (10/10) * (1-0) = 1.0
    entity = Entity(identifier="test", reliability=10.0, ablative=0.0)
    assert entity.effectiveness() == pytest.approx(1.0)

    # Half effectiveness: 10 reliability, 0.5 ablative -> (10/10) * (1-0.5) = 0.5
    entity = Entity(identifier="test", reliability=10.0, ablative=0.5)
    assert entity.effectiveness() == pytest.approx(0.5)

    # Half effectiveness: 5 reliability, 0 ablative -> (5/10) * (1-0) = 0.5
    entity = Entity(identifier="test", reliability=5.0, ablative=0.0)
    assert entity.effectiveness() == pytest.approx(0.5)

    # Zero effectiveness: 5 reliability, 0.5 ablative -> (5/10) * (1-0.5) = 0.25
    entity = Entity(identifier="test", reliability=5.0, ablative=0.5)
    assert entity.effectiveness() == pytest.approx(0.25)

    # Fully degraded: 10 reliability, 1.0 ablative -> (10/10) * (1-1) = 0.0
    entity = Entity(identifier="test", reliability=10.0, ablative=1.0)
    assert entity.effectiveness() == pytest.approx(0.0)
