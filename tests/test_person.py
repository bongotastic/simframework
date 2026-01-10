from simframework.entity import Entity, Person
from simframework.engine import SimulationEngine


def test_person_entity_basic():
    eng = SimulationEngine()
    p = Person(essence="alice")
    eng.add_entity(p, "alice")
    assert eng.get_entity("alice") is p
    assert p.name == "alice"


def test_entity_location_field():
    # Entities can hold arbitrary location references (opaque objects).
    eng = SimulationEngine()
    loc = object()
    e = Entity("item")
    e.location = loc
    eng.add_entity(e, "item1")
    assert eng.get_entity("item1").location is loc
