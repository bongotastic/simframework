from simframework.system import SystemTemplate, AgentTemplate, SystemInstance, Agent


def test_template_labels_and_location():
    tmpl = SystemTemplate("module", properties={"capacity": 2}, labels=["module", "habitat"], is_location=True)
    inst = tmpl.instantiate(instance_id="mod-1")
    assert isinstance(inst, SystemInstance)
    assert inst.labels == ["module", "habitat"]
    assert inst.is_location is True

    a_tmpl = AgentTemplate("astronaut", labels=["crew", "human"])
    a = a_tmpl.instantiate(instance_id="astro-99")
    assert isinstance(a, Agent)
    assert a.labels == ["crew", "human"]
