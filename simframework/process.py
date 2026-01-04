"""Process definitions and data structures for simulation workflows.

Processes define how inputs transform into outputs via requirements (tools, labor, infrastructure).
Supports both manual and natural processes with time variants keyed by taxonomy item.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ProcessType(Enum):
    """Process execution model."""
    MANUAL = "manual"
    NATURAL = "natural"


@dataclass
class ProcessIO:
    """Flexible taxonomy-based IO item with optional properties.
    
    Base wrapper for any process input/output/requirement that references
    a taxonomy item. Properties dict enables extensibility without class changes.
    """
    item: str  # Taxonomy path (e.g., "item/organic/plant/grain")
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Retrieve a property by key with fallback."""
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any) -> None:
        """Set or update a property."""
        self.properties[key] = value


@dataclass
class RequirementTool(ProcessIO):
    """Tool requirement: item + mean-time-between-failures (mtbf).
    
    mtbf: Mean time until failure (hours). Tracks tool wear/degradation risk.
    """
    def __post_init__(self):
        # Ensure mtbf is set; default from properties or None
        if 'mtbf' not in self.properties:
            self.properties['mtbf'] = None
    
    @property
    def mtbf(self) -> Optional[float]:
        return self.get_property('mtbf')
    
    @mtbf.setter
    def mtbf(self, value: Optional[float]) -> None:
        self.set_property('mtbf', value)


@dataclass
class RequirementLabor(ProcessIO):
    """Labor requirement: role + skill + worker count.
    
    role: Taxonomy path to a social role (e.g., "social/role/baker")
    skill: Taxonomy path to a fallback skill if no role-specific one exists
    count: Ideal number of workers for this role
    """
    def __post_init__(self):
        if 'skill' not in self.properties:
            self.properties['skill'] = None
        if 'count' not in self.properties:
            self.properties['count'] = 1
    
    @property
    def role(self) -> str:
        return self.item
    
    @role.setter
    def role(self, value: str) -> None:
        self.item = value
    
    @property
    def skill(self) -> Optional[str]:
        return self.get_property('skill')
    
    @skill.setter
    def skill(self, value: Optional[str]) -> None:
        self.set_property('skill', value)
    
    @property
    def count(self) -> int:
        return self.get_property('count', 1)
    
    @count.setter
    def count(self, value: int) -> None:
        self.set_property('count', value)


@dataclass
class RequirementAnimal(ProcessIO):
    """Animal requirement: role (animal taxonomy) + properties + count.
    
    role: Taxonomy path to animal type/variant
    properties: Dict of arbitrary properties (e.g., {"state": "working"})
    count: Number of animals needed
    """
    def __post_init__(self):
        if 'count' not in self.properties:
            self.properties['count'] = 1
    
    @property
    def role(self) -> str:
        return self.item
    
    @role.setter
    def role(self, value: str) -> None:
        self.item = value
    
    @property
    def count(self) -> int:
        return self.get_property('count', 1)
    
    @count.setter
    def count(self, value: int) -> None:
        self.set_property('count', value)


@dataclass
class RequirementInfrastructure(ProcessIO):
    """Infrastructure requirement: single item (building/structure).
    
    item: Taxonomy path to structure (e.g., "item/structure/bakehouse")
    """
    pass


# Polymorphic union type for requirements
ProcessRequirement = Union[RequirementTool, RequirementLabor, RequirementAnimal, RequirementInfrastructure]


@dataclass
class ProcessDuration:
    """Time specification: base duration + optional item-specific variants.
    
    base_duration: Default duration in hours
    variants: Dict mapping taxonomy item path -> specific duration (hours)
    """
    base_duration: float
    variants: Dict[str, float] = field(default_factory=dict)
    
    def get_duration(self, item: Optional[str] = None) -> float:
        """Get duration for a specific item, or base if not found."""
        if item and item in self.variants:
            return self.variants[item]
        return self.base_duration


@dataclass
class ProcessIO_Input(ProcessIO):
    """Input/output item with optional quantity and variants.
    
    item: Taxonomy path
    quantity: Base quantity (mass, count, etc.). Defaults to 1.0
    quantity_variants: Dict mapping taxonomy item -> specific quantity
    properties: Extensible property dict
    """
    def __post_init__(self):
        if 'quantity' not in self.properties:
            self.properties['quantity'] = 1.0
        if 'quantity_variants' not in self.properties:
            self.properties['quantity_variants'] = {}
    
    @property
    def quantity(self) -> float:
        return self.get_property('quantity', 1.0)
    
    @quantity.setter
    def quantity(self, value: float) -> None:
        self.set_property('quantity', value)
    
    @property
    def quantity_variants(self) -> Dict[str, float]:
        return self.get_property('quantity_variants', {})
    
    @quantity_variants.setter
    def quantity_variants(self, value: Dict[str, float]) -> None:
        self.set_property('quantity_variants', value)
    
    def get_quantity(self, item: Optional[str] = None) -> float:
        """Get quantity for a specific item, or base if not found."""
        if item and item in self.quantity_variants:
            return self.quantity_variants[item]
        return self.quantity


@dataclass
class Process:
    """Complete process definition: transformations, requirements, time.
    
    Attributes:
        path: Unique taxonomy-like identifier (e.g., "process/production/forging")
        name: Human-readable name
        process_type: MANUAL or NATURAL
        duration: ProcessDuration with base and variants
        requirements: List of ProcessRequirement (tools, labor, animals, infrastructure)
        inputs: List of ProcessIO_Input items consumed/transformed
        outputs: List of ProcessIO_Input items produced
        waste: List of ProcessIO_Input byproducts
    """
    path: str
    name: str
    process_type: ProcessType
    duration: ProcessDuration
    requirements: List[ProcessRequirement] = field(default_factory=list)
    inputs: List[ProcessIO_Input] = field(default_factory=list)
    outputs: List[ProcessIO_Input] = field(default_factory=list)
    waste: List[ProcessIO_Input] = field(default_factory=list)
    
    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> "Process":
        """Deserialize a Process from YAML-loaded dict.
        
        Expected structure:
            path: str
            name: str
            type: "manual" | "natural"
            time:
                base_duration: float
                by_plant?: {taxonomy_item: duration, ...}
                mtbf?: float (for natural processes)
            requirements?:
                infrastructure?: str | list
                tools?: list of {item, mtbf?}
                labor?: list of {role, skill?, count?}
                animals?: list of {role, properties?, count?}
            inputs?:
                materials?: list of {item, quantity?, quantity_by_plant?}
            outputs?:
                products?: list of {item, quantity?, quantity_by_plant?, quantity_base?, skill_modifier?}
                waste?: list of {item, quantity?, quantity_by_plant?}
        """
        path = data.get("path", "")
        name = data.get("name", "")
        proc_type_str = data.get("type", "manual").lower()
        process_type = ProcessType.MANUAL if proc_type_str == "manual" else ProcessType.NATURAL
        
        # Parse duration
        time_spec = data.get("time", {})
        base_dur = float(time_spec.get("base_duration", time_spec.get("mtbf", 0.0)))
        variants = time_spec.get("by_plant", {})
        duration = ProcessDuration(base_duration=base_dur, variants=variants)
        
        # Parse requirements
        requirements = []
        reqs = data.get("requirements", {})
        
        # Infrastructure
        if "infrastructure" in reqs:
            infra = reqs["infrastructure"]
            if isinstance(infra, str):
                requirements.append(RequirementInfrastructure(item=infra))
            elif isinstance(infra, list):
                for item in infra:
                    requirements.append(RequirementInfrastructure(item=item if isinstance(item, str) else item.get("item", "")))
        
        # Tools
        for tool_spec in reqs.get("tools", []):
            item = tool_spec.get("item", "")
            mtbf = tool_spec.get("mtbf")
            req = RequirementTool(item=item)
            if mtbf is not None:
                req.mtbf = mtbf
            requirements.append(req)
        
        # Labor
        for labor_spec in reqs.get("labor", []):
            role = labor_spec.get("role", "")
            skill = labor_spec.get("skill")
            count = labor_spec.get("count", 1)
            req = RequirementLabor(item=role)
            req.skill = skill
            req.count = count
            requirements.append(req)
        
        # Animals
        for animal_spec in reqs.get("animals", []):
            role = animal_spec.get("role", "")
            count = animal_spec.get("count", 1)
            props = animal_spec.get("properties", [])
            # Convert properties list to dict if needed
            props_dict = {}
            if isinstance(props, list):
                for p in props:
                    if isinstance(p, dict):
                        props_dict.update(p)
                    else:
                        props_dict["item"] = p
            elif isinstance(props, dict):
                props_dict = props
            
            req = RequirementAnimal(item=role, properties=props_dict)
            req.count = count
            requirements.append(req)
        
        # Parse inputs
        inputs = []
        input_spec = data.get("inputs", {})
        for item_spec in input_spec.get("materials", []):
            item = item_spec.get("item", "")
            quantity = item_spec.get("quantity", 1.0)
            quantity_vars = item_spec.get("quantity_by_plant", {})
            io = ProcessIO_Input(item=item)
            io.quantity = quantity
            io.quantity_variants = quantity_vars
            inputs.append(io)
        
        # Parse outputs
        outputs = []
        output_spec = data.get("outputs", {})
        for item_spec in output_spec.get("products", []):
            item = item_spec.get("item", "")
            quantity = item_spec.get("quantity", item_spec.get("quantity_base", 1.0))
            quantity_vars = item_spec.get("quantity_by_plant", {})
            io = ProcessIO_Input(item=item)
            io.quantity = quantity
            io.quantity_variants = quantity_vars
            # Store optional skill_modifier
            if "skill_modifier" in item_spec:
                io.set_property("skill_modifier", item_spec["skill_modifier"])
            outputs.append(io)
        
        # Parse waste
        waste = []
        for item_spec in output_spec.get("waste", []):
            item = item_spec.get("item", "")
            quantity = item_spec.get("quantity", 1.0)
            quantity_vars = item_spec.get("quantity_by_plant", {})
            io = ProcessIO_Input(item=item)
            io.quantity = quantity
            io.quantity_variants = quantity_vars
            waste.append(io)
        
        return cls(
            path=path,
            name=name,
            process_type=process_type,
            duration=duration,
            requirements=requirements,
            inputs=inputs,
            outputs=outputs,
            waste=waste
        )
    
    def get_duration(self, item: Optional[str] = None) -> float:
        """Get process duration, optionally specific to a taxonomy item."""
        return self.duration.get_duration(item)

    def has_input(self, identifier: str) -> bool:
        """Return True if this process has an input that matches `identifier`.

        Matching logic:
        - If an input's item equals `identifier`, it's a match.
        - If an input has `quantity_variants` containing `identifier` as a key, it's a match.
        """
        if not identifier:
            return False
        for io in self.inputs:
            try:
                if getattr(io, "item", None) == identifier:
                    return True
                qvars = getattr(io, "quantity_variants", None)
                if isinstance(qvars, dict) and identifier in qvars:
                    return True
            except Exception:
                continue
        return False

    def has_output(self, identifier: str) -> bool:
        """Return True if this process has an output that matches `identifier`.

        Matching logic mirrors `has_input`:
        - If an output's item equals `identifier`, it's a match.
        - If an output has `quantity_variants` containing `identifier` as a key, it's a match.
        """
        if not identifier:
            return False
        for io in self.outputs:
            try:
                if getattr(io, "item", None) == identifier:
                    return True
                qvars = getattr(io, "quantity_variants", None)
                if isinstance(qvars, dict) and identifier in qvars:
                    return True
            except Exception:
                continue
        return False

    def has_requirement(self, identifier: str) -> bool:
        """Return True if this process has a requirement matching `identifier`.

        Matching logic:
        - If a requirement's `item` equals `identifier`, it's a match. This
          covers tools, infrastructure, labor (role), and animals (role).
        """
        if not identifier:
            return False
        for req in self.requirements:
            try:
                if getattr(req, "item", None) == identifier:
                    return True
                # Some requirements may store role as 'role' in properties
                role = req.get_property("role") if hasattr(req, "get_property") else None
                if role == identifier:
                    return True
            except Exception:
                continue
        return False

    def __repr__(self) -> str:
        return f"Process(path={self.path!r}, type={self.process_type.value}, duration={self.duration.base_duration}h, reqs={len(self.requirements)}, inputs={len(self.inputs)}, outputs={len(self.outputs)})"
