import datetime
from datetime import timedelta

try:
    from simframework.engine import SimulationEngine
    from simframework.system import SystemTemplate, Agent, AgentTemplate
    from simframework.event import Event
    from simframework.entity import Entity
    from simframework.scope import Scope
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.engine import SimulationEngine
    from simframework.system import SystemTemplate, Agent, AgentTemplate
    from simframework.event import Event
    from simframework.entity import Entity
    from simframework.scope import Scope


class TestAgentBehavior:
    def test_agent_perceive_entities(self):
        eng = SimulationEngine()
        e1 = Entity("target")
        e2 = Entity("other")
        eng.add_entity(e1, "target1")
        eng.add_entity(e2, "other1")

        tmpl = SystemTemplate("agent_tmpl")
        a = Agent(template=tmpl, id="agent1")
        eng.add_agent(a)

        seen = a.perceive_entities(eng, predicate=lambda e: "target" in e.name)
        assert len(seen) == 1
        assert seen[0].name == "target"

    def test_agent_location_perception(self):
        eng = SimulationEngine()
        # Create a station and one module instance to act as a location
        st_t = SystemTemplate("station")
        st = st_t.instantiate(instance_id="station-0")
        mod_t = SystemTemplate("module")
        mod = mod_t.instantiate(instance_id="module-1", parent=st)
        st.add_child(mod)

        # Create two entities and place one in the module
        e_in = Entity("inside")
        e_out = Entity("outside")
        e_in.location = mod
        e_out.location = st
        eng.add_entity(e_in, "e_in")
        eng.add_entity(e_out, "e_out")

        tmpl = SystemTemplate("agent_tmpl")
        a = Agent(template=tmpl, id="agent2")
        eng.add_agent(a)

        # No location -> sees both
        seen_all = a.perceive_entities(eng)
        assert len(seen_all) == 2

        # Set agent location to the module -> sees only the co-located entity
        a.set_location(mod)
        seen_local = a.perceive_entities(eng)
        assert len(seen_local) == 1
        assert seen_local[0].name == "inside"

    def test_agent_interact_with_system(self):
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        eng = SimulationEngine(start_time=start)
        tmpl = SystemTemplate("node")
        n1 = tmpl.instantiate(instance_id="n1")
        eng.add_system_instance(n1)

        tmpl_a = SystemTemplate("agent_tmpl")
        a = Agent(template=tmpl_a, id="a1")
        eng.add_agent(a)

        # Agent schedules an interaction on system n1
        a.interact_with_system(eng, "n1", 5.0, lambda: None)
        peeked = eng.scheduler.peek_events(system=n1)
        assert len(peeked) == 1
        run_at, ev = peeked[0]
        assert run_at == start + timedelta(seconds=5.0)
        assert ev.system == n1

    def test_agent_goals_and_tasks(self):
        tmpl = SystemTemplate("agent_tmpl")
        a = Agent(template=tmpl, id="a2")
        assert a.pop_goal() is None
        a.add_goal("explore")
        a.add_goal("gather")
        assert a.pop_goal() == "explore"

        task_scope = Scope("exploration")
        a.assign_task(task_scope)
        assert a.current_task == task_scope

    def test_agent_template_instantiation(self):
        # AgentTemplate should instantiate Agent instances and children
        tmpl = AgentTemplate("scout", properties={"vision": {"default": 10, "transitive": True}})
        child_t = SystemTemplate("sensor", properties={"range": 100})
        tmpl.add_child(child_t)

        a = tmpl.instantiate(instance_id="scout-1")
        assert isinstance(a, Agent)
        assert a.id == "scout-1"
        assert len(a.children) == 1
        child = a.children[0]
        assert child.template.name == "sensor"
        # Transitive property from agent template should be available to child
        assert child.get_property("vision") == 10
