"""Tests for Process data structures."""

import pytest
from simframework.process import (
    ProcessType,
    ProcessIO,
    RequirementTool,
    RequirementLabor,
    RequirementAnimal,
    RequirementInfrastructure,
    ProcessDuration,
    ProcessIO_Input,
    Process,
)


class TestProcessIO:
    def test_create_basic(self):
        io = ProcessIO(item="item/goods/hammer")
        assert io.item == "item/goods/hammer"
        assert io.properties == {}
    
    def test_property_access(self):
        io = ProcessIO(item="item/goods/hammer")
        io.set_property("mtbf", 500.0)
        assert io.get_property("mtbf") == 500.0
        assert io.get_property("nonexistent", "default") == "default"


class TestRequirementTool:
    def test_create_with_mtbf(self):
        tool = RequirementTool(item="goods/tools/hammer")
        tool.mtbf = 600.0
        assert tool.mtbf == 600.0
        assert tool.item == "goods/tools/hammer"
    
    def test_mtbf_property(self):
        tool = RequirementTool(item="goods/tools/anvil", properties={"mtbf": 5000.0})
        assert tool.mtbf == 5000.0


class TestRequirementLabor:
    def test_create_labor(self):
        labor = RequirementLabor(item="social/role/baker")
        labor.skill = "attributes/skill/provisioning"
        labor.count = 2
        assert labor.role == "social/role/baker"
        assert labor.skill == "attributes/skill/provisioning"
        assert labor.count == 2
    
    def test_labor_default_count(self):
        labor = RequirementLabor(item="social/role/peasant")
        assert labor.count == 1


class TestRequirementAnimal:
    def test_create_animal(self):
        animal = RequirementAnimal(item="source/animal/domestic/ox")
        animal.count = 2
        assert animal.role == "source/animal/domestic/ox"
        assert animal.count == 2
    
    def test_animal_with_properties(self):
        animal = RequirementAnimal(
            item="source/animal/domestic/ox",
            properties={"working": True}
        )
        assert animal.get_property("working") is True


class TestRequirementInfrastructure:
    def test_create_infrastructure(self):
        infra = RequirementInfrastructure(item="item/structure/bakehouse")
        assert infra.item == "item/structure/bakehouse"


class TestProcessDuration:
    def test_base_duration(self):
        dur = ProcessDuration(base_duration=8.0)
        assert dur.get_duration() == 8.0
        assert dur.get_duration("any_item") == 8.0
    
    def test_duration_variants(self):
        dur = ProcessDuration(
            base_duration=16.0,
            variants={
                "source/plant/species/cereal/wheat": 16.0,
                "source/plant/species/legume/pea": 12.0,
            }
        )
        assert dur.get_duration("source/plant/species/cereal/wheat") == 16.0
        assert dur.get_duration("source/plant/species/legume/pea") == 12.0
        assert dur.get_duration("unknown") == 16.0


class TestProcessIOInput:
    def test_basic_io(self):
        io = ProcessIO_Input(item="item/organic/plant/grain")
        assert io.quantity == 1.0
        assert io.quantity_variants == {}
    
    def test_quantity_variants(self):
        io = ProcessIO_Input(item="item/organic/plant/sheaf")
        io.quantity = 100.0
        io.quantity_variants = {
            "source/plant/species/cereal/wheat": 700.0,
            "source/plant/species/legume/pea": 1000.0,
        }
        assert io.get_quantity("source/plant/species/cereal/wheat") == 700.0
        assert io.get_quantity("source/plant/species/legume/pea") == 1000.0
        assert io.get_quantity("unknown") == 100.0


class TestProcessFromYAML:
    def test_simple_natural_process(self):
        data = {
            "path": "process/spoilage/flour",
            "name": "Flour Spoilage",
            "type": "natural",
            "time": {"mtbf": 4000.0},
            "inputs": {
                "materials": [{"item": "item/organic/plant/flour"}]
            },
            "outputs": {
                "products": [{"item": "item/organic/waste/rotting_matter"}]
            },
        }
        proc = Process.from_yaml_dict(data)
        assert proc.path == "process/spoilage/flour"
        assert proc.name == "Flour Spoilage"
        assert proc.process_type == ProcessType.NATURAL
        assert proc.duration.base_duration == 4000.0
        assert len(proc.inputs) == 1
        assert proc.inputs[0].item == "item/organic/plant/flour"
        assert len(proc.outputs) == 1
    
    def test_manual_process_with_requirements(self):
        data = {
            "path": "process/production/forging_horseshoes",
            "name": "Forging Horseshoes",
            "type": "manual",
            "time": {"base_duration": 2.0},
            "requirements": {
                "infrastructure": "structure/smithy_forge",
                "tools": [
                    {"item": "goods/tools/crafts/smithing/hammer", "mtbf": 600.0},
                    {"item": "goods/tools/crafts/smithing/anvil", "mtbf": 5000.0},
                ],
                "labor": [
                    {"role": "social/role/blacksmith", "skill": "attributes/skill/smithing", "count": 1}
                ],
            },
            "inputs": {
                "materials": [
                    {"item": "item/goods/stock/metal/wrought_iron", "quantity": 1.5}
                ]
            },
            "outputs": {
                "products": [
                    {"item": "goods/tools/transport/tack/horseshoe", "quantity_base": 4}
                ]
            },
        }
        proc = Process.from_yaml_dict(data)
        assert proc.process_type == ProcessType.MANUAL
        assert len(proc.requirements) == 4  # 1 infrastructure + 2 tools + 1 labor
        
        # Find infrastructure requirement
        infra_reqs = [r for r in proc.requirements if isinstance(r, RequirementInfrastructure)]
        assert len(infra_reqs) == 1
        assert infra_reqs[0].item == "structure/smithy_forge"
        
        # Find tool requirements
        tool_reqs = [r for r in proc.requirements if isinstance(r, RequirementTool)]
        assert len(tool_reqs) == 2
        assert any(t.mtbf == 600.0 for t in tool_reqs)
        
        # Find labor requirements
        labor_reqs = [r for r in proc.requirements if isinstance(r, RequirementLabor)]
        assert len(labor_reqs) == 1
        assert labor_reqs[0].role == "social/role/blacksmith"
        assert labor_reqs[0].skill == "attributes/skill/smithing"
        assert labor_reqs[0].count == 1
    
    def test_process_with_variants(self):
        data = {
            "path": "process/cultivation/harvesting",
            "name": "Generic Harvesting",
            "type": "manual",
            "time": {
                "base_duration": 16.0,
                "by_plant": {
                    "source/plant/species/cereal/wheat": 16.0,
                    "source/plant/species/legume/pea": 12.0,
                },
            },
            "outputs": {
                "products": [
                    {
                        "item": "item/organic/plant/sheaf",
                        "quantity_by_plant": {
                            "source/plant/species/cereal/wheat": 700.0,
                            "source/plant/species/legume/pea": 1000.0,
                        },
                    }
                ]
            },
        }
        proc = Process.from_yaml_dict(data)
        assert proc.get_duration("source/plant/species/cereal/wheat") == 16.0
        assert proc.get_duration("source/plant/species/legume/pea") == 12.0
        assert proc.outputs[0].get_quantity("source/plant/species/cereal/wheat") == 700.0
        assert proc.outputs[0].get_quantity("source/plant/species/legume/pea") == 1000.0
    
    def test_process_with_animals(self):
        data = {
            "path": "process/cultivation/ploughing",
            "name": "Ploughing",
            "type": "manual",
            "time": {"base_duration": 8.0},
            "requirements": {
                "animals": [
                    {
                        "role": "source/animal/domestic/ox",
                        "properties": [{"working": True}],
                        "count": 2,
                    }
                ]
            },
        }
        proc = Process.from_yaml_dict(data)
        animal_reqs = [r for r in proc.requirements if isinstance(r, RequirementAnimal)]
        assert len(animal_reqs) == 1
        assert animal_reqs[0].role == "source/animal/domestic/ox"
        assert animal_reqs[0].count == 2
        assert animal_reqs[0].get_property("working") is True
    
    def test_process_with_waste(self):
        data = {
            "path": "process/production/forging",
            "name": "Forging",
            "type": "manual",
            "time": {"base_duration": 2.0},
            "outputs": {
                "products": [{"item": "goods/horseshoe", "quantity": 4}],
                "waste": [{"item": "item/organic/waste/slag", "quantity": 0.2}],
            },
        }
        proc = Process.from_yaml_dict(data)
        assert len(proc.outputs) == 1
        assert len(proc.waste) == 1
        assert proc.waste[0].item == "item/organic/waste/slag"
        assert proc.waste[0].quantity == 0.2


class TestProcessRepr:
    def test_repr(self):
        proc = Process(
            path="process/test",
            name="Test",
            process_type=ProcessType.MANUAL,
            duration=ProcessDuration(base_duration=5.0),
        )
        repr_str = repr(proc)
        assert "process/test" in repr_str
        assert "manual" in repr_str
        assert "5.0h" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
