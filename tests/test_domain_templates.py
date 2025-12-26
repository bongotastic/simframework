import tempfile
import yaml
from pathlib import Path

try:
    from simframework.scope import Domain
    from simframework.system import SystemTemplate, AgentTemplate
except ImportError:
    import sys
    from pathlib import Path
    pkg_root = Path(__file__).resolve().parents[1]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from simframework.scope import Domain
    from simframework.system import SystemTemplate, AgentTemplate


def test_load_system_and_agent_templates(tmp_path: Path):
    content = {
        "name": "TestDomain",
        "systems": [
            {
                "name": "machine",
                "properties": {"owner": {"default": "Factory", "transitive": True}},
                "children": [
                    {"name": "subassembly", "properties": {"serial": "CHILD-SN"}}
                ],
            }
        ],
        "agents": [
            {
                "name": "scout",
                "properties": {"vision": {"default": 10, "transitive": True}},
            }
        ],
    }
    p = tmp_path / "domain.yaml"
    p.write_text(yaml.safe_dump(content))

    d = Domain.from_yaml(str(p))
    assert d.name == "TestDomain"

    # system template
    assert "machine" in d.system_templates
    mt = d.get_system_template("machine")
    assert isinstance(mt, SystemTemplate)
    assert mt.property_spec("owner") is not None
    child = mt.children[0]
    assert child.name == "subassembly"

    # agent template
    assert "scout" in d.agent_templates
    at = d.get_agent_template("scout")
    assert isinstance(at, AgentTemplate)
    assert at.property_spec("vision") is not None
