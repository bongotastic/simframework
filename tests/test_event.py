from simframework.event import Event


def test_set_property_basic():
    e = Event()
    e.set_property("foo", "bar")
    assert e.data["foo"] == "bar"


def test_set_property_overwrite():
    e = Event(data={"a": 1})
    e.set_property("a", 2)
    assert e.data["a"] == 2


def test_set_property_non_str_key():
    # keys are allowed to be non-strings if user wants; ensure it stores as given
    e = Event()
    e.set_property(42, "meaning")
    assert e.data[42] == "meaning"


def test_get_property_existing():
    e = Event(data={"x": 10})
    assert e.get_property("x") == 10


def test_get_property_missing_returns_none():
    e = Event()
    assert e.get_property("missing") is None


def test_get_property_missing_with_default():
    e = Event()
    assert e.get_property("missing", default=123) == 123
