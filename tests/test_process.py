"""Tests for Process data structures."""

import pytest
from simframework.process import (
    ProcessItem,
    Requirement,
    Input,
    Output,
    Transform,
    Process,
)


class TestProcessItem:
    def test_create_basic(self):
        item = ProcessItem(name="Test", scope="item/goods/hammer")
        assert item.name == "Test"
        assert item.scope == "item/goods/hammer"
        assert item.material is None
        assert item.quantity == 1.0
        assert item.properties == []
    
    def test_to_dict(self):
        item = ProcessItem(
            name="Test",
            scope="item/goods/hammer",
            material="source/material/iron",
            quantity=2.0,
            properties=["property/heavy"]
        )
        d = item.to_dict()
        assert d["name"] == "Test"
        assert d["scope"] == "item/goods/hammer"
        assert d["material"] == "source/material/iron"
        assert d["quantity"] == 2.0
        assert d["properties"] == ["property/heavy"]


class TestRequirement:
    def test_create_with_mtbf(self):
        req = Requirement(
            name="Hammer",
            scope="item/tool/hammer",
            mtbf=600.0
        )
        assert req.name == "Hammer"
        assert req.scope == "item/tool/hammer"
        assert req.mtbf == 600.0
    
    def test_to_dict_includes_mtbf(self):
        req = Requirement(
            name="Hammer",
            scope="item/tool/hammer",
            material="source/material/steel",
            mtbf=600.0,
            quantity=1,
            properties=["property/heavy"]
        )
        d = req.to_dict()
        assert d["mtbf"] == 600.0
        assert d["material"] == "source/material/steel"


class TestTransform:
    def test_create_transform(self):
        trans = Transform(
            name="Workpiece",
            scope="item/component/blade_blank",
            material="source/material/iron",
            properties=["property/annealed"],
            add_properties=["property/shaped"],
            remove_properties=["property/annealed"],
            new_scope="item/component/blade"
        )
        assert trans.name == "Workpiece"
        assert trans.add_properties == ["property/shaped"]
        assert trans.remove_properties == ["property/annealed"]
        assert trans.new_scope == "item/component/blade"
    
    def test_to_dict(self):
        trans = Transform(
            name="Workpiece",
            scope="item/component/blade_blank",
            add_properties=["property/shaped"],
            remove_properties=["property/annealed"],
            new_scope="item/component/blade",
            new_material="source/material/steel"
        )
        d = trans.to_dict()
        assert d["add_properties"] == ["property/shaped"]
        assert d["remove_properties"] == ["property/annealed"]
        assert d["new_scope"] == "item/component/blade"
        assert d["new_material"] == "source/material/steel"


class TestProcess:
    def test_create_basic(self):
        proc = Process(path="process/test", name="Test Process")
        assert proc.path == "process/test"
        assert proc.name == "Test Process"
        assert proc.base_duration == 0.0
        assert proc.requirements == []
        assert proc.inputs == []
        assert proc.transforms == []
        assert proc.outputs == []
    
    def test_get_duration_base(self):
        proc = Process(
            path="process/test",
            name="Test",
            base_duration=4.0
        )
        assert proc.get_duration() == 4.0
        assert proc.get_duration("") == 4.0
        assert proc.get_duration("unknown/material") == 4.0
    
    def test_get_duration_by_material(self):
        proc = Process(
            path="process/test",
            name="Test",
            base_duration=4.0,
            by_material={
                "source/material/iron": 4.0,
                "source/material/steel": 6.0,
                "source/material/titanium": 12.0,
            }
        )
        assert proc.get_duration() == 4.0
        assert proc.get_duration("source/material/iron") == 4.0
        assert proc.get_duration("source/material/steel") == 6.0
        assert proc.get_duration("source/material/titanium") == 12.0
        assert proc.get_duration("source/material/unknown") == 4.0
    
    def test_get_requirements_all(self):
        proc = Process(
            path="process/test",
            name="Test",
            requirements=[
                Requirement(name="Hammer", scope="item/tool/hammer"),
                Requirement(name="Forge", scope="item/infrastructure/forge"),
            ]
        )
        scopes = proc.get_requirements()
        assert scopes == ["item/tool/hammer", "item/infrastructure/forge"]
    
    def test_get_requirements_by_scope(self):
        proc = Process(
            path="process/test",
            name="Test",
            requirements=[
                Requirement(
                    name="Hammer",
                    scope="item/tool/hammer",
                    material="source/material/steel",
                    mtbf=600.0,
                    quantity=1,
                    properties=["property/heavy"]
                ),
            ]
        )
        req_dict = proc.get_requirements("item/tool/hammer")
        assert req_dict is not None
        assert req_dict["name"] == "Hammer"
        assert req_dict["scope"] == "item/tool/hammer"
        assert req_dict["material"] == "source/material/steel"
        assert req_dict["mtbf"] == 600.0
        assert req_dict["quantity"] == 1
        assert req_dict["properties"] == ["property/heavy"]
        
        # Non-existent scope returns None
        assert proc.get_requirements("item/tool/anvil") is None
    
    def test_has_requirement(self):
        proc = Process(
            path="process/test",
            name="Test",
            requirements=[
                Requirement(name="Hammer", scope="item/tool/hammer"),
            ]
        )
        assert proc.has_requirement("item/tool/hammer") is True
        assert proc.has_requirement("item/tool") is True
        assert proc.has_requirement("item") is True
        assert proc.has_requirement("item/tool/anvil") is False
    
    def test_get_inputs_all(self):
        proc = Process(
            path="process/test",
            name="Test",
            inputs=[
                Input(name="Fuel", scope="item/consumable/fuel"),
                Input(name="Ore", scope="item/material/ore"),
            ]
        )
        scopes = proc.get_inputs()
        assert scopes == ["item/consumable/fuel", "item/material/ore"]
    
    def test_get_inputs_by_scope(self):
        proc = Process(
            path="process/test",
            name="Test",
            inputs=[
                Input(
                    name="Fuel",
                    scope="item/consumable/fuel",
                    material="source/material/coal",
                    quantity=5.0
                ),
            ]
        )
        inp_dict = proc.get_inputs("item/consumable/fuel")
        assert inp_dict is not None
        assert inp_dict["name"] == "Fuel"
        assert inp_dict["quantity"] == 5.0
        assert inp_dict["material"] == "source/material/coal"
        
        assert proc.get_inputs("item/consumable/wood") is None
    
    def test_has_input(self):
        proc = Process(
            path="process/test",
            name="Test",
            inputs=[
                Input(name="Fuel", scope="item/consumable/fuel"),
            ]
        )
        assert proc.has_input("item/consumable/fuel") is True
        assert proc.has_input("item/consumable") is True
        assert proc.has_input("item/consumable/wood") is False
    
    def test_get_transforms_all(self):
        proc = Process(
            path="process/test",
            name="Test",
            transforms=[
                Transform(name="Workpiece", scope="item/component/blade_blank"),
            ]
        )
        scopes = proc.get_transforms()
        assert scopes == ["item/component/blade_blank"]
    
    def test_get_transforms_by_scope(self):
        proc = Process(
            path="process/test",
            name="Test",
            transforms=[
                Transform(
                    name="Workpiece",
                    scope="item/component/blade_blank",
                    add_properties=["property/shaped"],
                    remove_properties=["property/annealed"],
                    new_scope="item/component/blade"
                ),
            ]
        )
        trans_dict = proc.get_transforms("item/component/blade_blank")
        assert trans_dict is not None
        assert trans_dict["add_properties"] == ["property/shaped"]
        assert trans_dict["remove_properties"] == ["property/annealed"]
        assert trans_dict["new_scope"] == "item/component/blade"
    
    def test_has_transform(self):
        proc = Process(
            path="process/test",
            name="Test",
            transforms=[
                Transform(name="Workpiece", scope="item/component/blade_blank"),
            ]
        )
        assert proc.has_transform("item/component/blade_blank") is True
        assert proc.has_transform("item/component") is True
        assert proc.has_transform("item/component/other") is False
    
    def test_get_outputs_all(self):
        proc = Process(
            path="process/test",
            name="Test",
            outputs=[
                Output(name="Slag", scope="item/waste/slag"),
            ]
        )
        scopes = proc.get_outputs()
        assert scopes == ["item/waste/slag"]
    
    def test_get_outputs_by_scope(self):
        proc = Process(
            path="process/test",
            name="Test",
            outputs=[
                Output(
                    name="Slag",
                    scope="item/waste/slag",
                    material="source/material/iron_oxide",
                    quantity=0.5,
                    properties=["property/hot"]
                ),
            ]
        )
        out_dict = proc.get_outputs("item/waste/slag")
        assert out_dict is not None
        assert out_dict["name"] == "Slag"
        assert out_dict["quantity"] == 0.5
        assert out_dict["material"] == "source/material/iron_oxide"
        assert out_dict["properties"] == ["property/hot"]
    
    def test_has_output(self):
        proc = Process(
            path="process/test",
            name="Test",
            outputs=[
                Output(name="Slag", scope="item/waste/slag"),
            ]
        )
        assert proc.has_output("item/waste/slag") is True
        assert proc.has_output("item/waste") is True
        assert proc.has_output("item/waste/other") is False


class TestProcessFromYAML:
    def test_full_template_parse(self):
        """Test parsing a complete YAML structure matching the template."""
        data = {
            "path": "process/manufacturing/example_forging",
            "name": "Example Robust Process",
            "time": {
                "base_duration": 4.0,
                "by_material": {
                    "source/material/iron": 4.0,
                    "source/material/steel": 6.0,
                    "source/material/titanium": 12.0,
                }
            },
            "requirements": [
                {
                    "name": "Impact Tool",
                    "scope": "item/tool/hammer",
                    "material": "source/material/hardened_steel",
                    "mtbf": 150.0,
                    "quantity": 1,
                    "properties": ["property/heavy", "property/durable"]
                },
                {
                    "name": "Heat Source",
                    "scope": "item/infrastructure/forge",
                    "properties": ["property/active", "property/hot"]
                }
            ],
            "inputs": [
                {
                    "name": "Fuel",
                    "scope": "item/consumable/fuel",
                    "material": "source/material/coal",
                    "quantity": 5.0
                }
            ],
            "transforms": [
                {
                    "name": "Workpiece",
                    "scope": "item/component/blade_blank",
                    "material": "source/material/iron",
                    "quantity": 1,
                    "properties": ["property/annealed"],
                    "add_properties": ["property/shaped", "property/compressed"],
                    "remove_properties": ["property/annealed", "property/rough_cast"],
                    "new_scope": "item/component/blade_blank3",
                    "new_material": "item/component/blade_blank2"
                }
            ],
            "outputs": [
                {
                    "name": "Slag Waste",
                    "scope": "item/waste/slag",
                    "material": "source/material/iron_oxide",
                    "properties": ["property/hot", "property/brittle"],
                    "quantity": 0.5
                }
            ]
        }
        
        proc = Process.from_yaml_dict(data)
        
        # Basic metadata
        assert proc.path == "process/manufacturing/example_forging"
        assert proc.name == "Example Robust Process"
        
        # Duration
        assert proc.get_duration() == 4.0
        assert proc.get_duration("source/material/steel") == 6.0
        assert proc.get_duration("source/material/titanium") == 12.0
        
        # Requirements
        assert len(proc.requirements) == 2
        req_scopes = proc.get_requirements()
        assert "item/tool/hammer" in req_scopes
        assert "item/infrastructure/forge" in req_scopes
        
        hammer_req = proc.get_requirements("item/tool/hammer")
        assert hammer_req["mtbf"] == 150.0
        assert hammer_req["material"] == "source/material/hardened_steel"
        
        # Inputs
        assert len(proc.inputs) == 1
        fuel_input = proc.get_inputs("item/consumable/fuel")
        assert fuel_input["quantity"] == 5.0
        assert fuel_input["material"] == "source/material/coal"
        
        # Transforms
        assert len(proc.transforms) == 1
        trans = proc.get_transforms("item/component/blade_blank")
        assert trans["add_properties"] == ["property/shaped", "property/compressed"]
        assert trans["remove_properties"] == ["property/annealed", "property/rough_cast"]
        assert trans["new_scope"] == "item/component/blade_blank3"
        
        # Outputs
        assert len(proc.outputs) == 1
        slag = proc.get_outputs("item/waste/slag")
        assert slag["quantity"] == 0.5
        assert slag["material"] == "source/material/iron_oxide"
    
    def test_minimal_process(self):
        """Test parsing a minimal process with only required fields."""
        data = {
            "path": "process/simple",
            "name": "Simple Process",
            "time": {
                "base_duration": 1.0
            }
        }
        
        proc = Process.from_yaml_dict(data)
        assert proc.path == "process/simple"
        assert proc.name == "Simple Process"
        assert proc.get_duration() == 1.0
        assert proc.get_requirements() == []
        assert proc.get_inputs() == []
        assert proc.get_transforms() == []
        assert proc.get_outputs() == []


class TestProcessRepr:
    def test_repr(self):
        proc = Process(
            path="process/test",
            name="Test",
            base_duration=5.0,
        )
        repr_str = repr(proc)
        assert "process/test" in repr_str
        assert "5.0h" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
