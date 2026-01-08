"""Process definitions and data structures for simulation workflows.

Processes define how inputs transform into outputs via requirements (tools, labor, infrastructure).
Supports time variants keyed by material taxonomy paths.

YAML Template Structure (domain_processes.template.yaml):
    path: process/manufacturing/example
    name: "Example Process"
    time:
        base_duration: 4.0
        by_material:
            source/material/iron: 4.0
            source/material/steel: 6.0
    requirements:
        - name: "Tool Name"
          scope: item/tool/hammer
          material: source/material/steel  # optional
          mtbf: 150.0                       # optional
          quantity: 1                       # optional
          properties:                       # optional
            - property/heavy
    inputs:
        - name: "Fuel"
          scope: item/consumable/fuel
          material: source/material/coal    # optional
          quantity: 5.0                     # optional
    transforms:
        - name: "Workpiece"
          scope: item/component/blade_blank
          material: source/material/iron    # optional
          quantity: 1                       # optional
          properties:                       # optional
            - property/annealed
          add_properties:                   # optional
            - property/shaped
          remove_properties:                # optional
            - property/annealed
          new_scope: item/component/blade   # optional
          new_material: source/material/x   # optional
    outputs:
        - name: "Slag Waste"
          scope: item/waste/slag
          material: source/material/iron_oxide  # optional
          quantity: 0.5                         # optional
          properties:                           # optional
            - property/hot
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProcessItem:
    """Base class for requirements, inputs, outputs, and transforms.
    
    All process items share a common structure:
    - name: Human-readable identifier
    - scope: Taxonomic path defining what type of item
    - material: Optional taxonomic path for material composition
    - quantity: Optional count/amount
    - properties: Optional list of taxonomic property paths
    """
    name: str
    scope: str
    material: Optional[str] = None
    quantity: float = 1.0
    properties: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary of all attributes."""
        result = {
            "name": self.name,
            "scope": self.scope,
            "quantity": self.quantity,
        }
        if self.material:
            result["material"] = self.material
        if self.properties:
            result["properties"] = self.properties.copy()
        return result


@dataclass
class Requirement(ProcessItem):
    """A requirement item (tool, infrastructure, etc.) not consumed.
    
    Additional attributes:
    - mtbf: Mean Time Between Failures (optional, for tools)
    """
    mtbf: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.mtbf is not None:
            result["mtbf"] = self.mtbf
        return result


@dataclass
class Input(ProcessItem):
    """An input item that is consumed by the process."""
    pass


@dataclass 
class Output(ProcessItem):
    """An output item produced by the process."""
    pass


@dataclass
class Transform(ProcessItem):
    """A transform item that is modified but retains identity.
    
    Additional attributes:
    - add_properties: List of property paths to add
    - remove_properties: List of property paths to remove
    - new_scope: Optional new scope after transformation
    - new_material: Optional new material after transformation
    """
    add_properties: List[str] = field(default_factory=list)
    remove_properties: List[str] = field(default_factory=list)
    new_scope: Optional[str] = None
    new_material: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.add_properties:
            result["add_properties"] = self.add_properties.copy()
        if self.remove_properties:
            result["remove_properties"] = self.remove_properties.copy()
        if self.new_scope:
            result["new_scope"] = self.new_scope
        if self.new_material:
            result["new_material"] = self.new_material
        return result


@dataclass
class Process:
    """Complete process definition following the YAML template structure.
    
    Attributes:
        path: Unique taxonomy-like identifier (e.g., "process/production/forging")
        name: Human-readable name
        base_duration: Default duration in hours
        by_material: Dict mapping material paths to specific durations
        requirements: List of Requirement items (tools, infrastructure)
        inputs: List of Input items (consumed)
        transforms: List of Transform items (modified in place)
        outputs: List of Output items (produced)
    """
    path: str
    name: str
    base_duration: float = 0.0
    by_material: Dict[str, float] = field(default_factory=dict)
    requirements: List[Requirement] = field(default_factory=list)
    inputs: List[Input] = field(default_factory=list)
    transforms: List[Transform] = field(default_factory=list)
    outputs: List[Output] = field(default_factory=list)
    
    # -------------------------------------------------------------------------
    # Duration API
    # -------------------------------------------------------------------------
    
    def get_duration(self, material: str = "") -> float:
        """Get process duration, optionally adjusted for a specific material.
        
        Args:
            material: Optional material taxonomy path to lookup specific duration.
        
        Returns:
            Duration in hours. If material is provided and found in by_material,
            returns that specific duration; otherwise returns base_duration.
        """
        if material and material in self.by_material:
            return self.by_material[material]
        return self.base_duration
    
    # -------------------------------------------------------------------------
    # Requirements API
    # -------------------------------------------------------------------------
    
    def get_requirements(self, scope: Optional[str] = None) -> Any:
        """Get requirements, optionally filtered by scope.
        
        Args:
            scope: If provided, return the attributes dict for the requirement
                   with this scope. If None, return list of all requirement scopes.
        
        Returns:
            - If scope is None: List of scope strings for all requirements.
            - If scope is provided: Dictionary of attributes for that requirement,
              or None if no requirement matches the scope.
        """
        if scope is None:
            return [r.scope for r in self.requirements]
        
        for req in self.requirements:
            if req.scope == scope:
                return req.to_dict()
        return None
    
    def has_requirement(self, identifier: str) -> bool:
        """Return True if any requirement's scope starts with identifier."""
        if not identifier:
            return False
        norm = identifier.strip("/")
        for req in self.requirements:
            if req.scope.strip("/").startswith(norm):
                return True
        return False
    
    # -------------------------------------------------------------------------
    # Inputs API
    # -------------------------------------------------------------------------
    
    def get_inputs(self, scope: Optional[str] = None) -> Any:
        """Get inputs, optionally filtered by scope.
        
        Args:
            scope: If provided, return the attributes dict for the input
                   with this scope. If None, return list of all input scopes.
        
        Returns:
            - If scope is None: List of scope strings for all inputs.
            - If scope is provided: Dictionary of attributes for that input,
              or None if no input matches the scope.
        """
        if scope is None:
            return [i.scope for i in self.inputs]
        
        for inp in self.inputs:
            if inp.scope == scope:
                return inp.to_dict()
        return None
    
    def has_input(self, identifier: str) -> bool:
        """Return True if any input's scope starts with identifier."""
        if not identifier:
            return False
        norm = identifier.strip("/")
        for inp in self.inputs:
            if inp.scope.strip("/").startswith(norm):
                return True
        return False
    
    # -------------------------------------------------------------------------
    # Transforms API
    # -------------------------------------------------------------------------
    
    def get_transforms(self, scope: Optional[str] = None) -> Any:
        """Get transforms, optionally filtered by scope.
        
        Args:
            scope: If provided, return the attributes dict for the transform
                   with this scope. If None, return list of all transform scopes.
        
        Returns:
            - If scope is None: List of scope strings for all transforms.
            - If scope is provided: Dictionary of attributes for that transform,
              or None if no transform matches the scope.
        """
        if scope is None:
            return [t.scope for t in self.transforms]
        
        for trans in self.transforms:
            if trans.scope == scope:
                return trans.to_dict()
        return None
    
    def has_transform(self, identifier: str) -> bool:
        """Return True if any transform's scope starts with identifier."""
        if not identifier:
            return False
        norm = identifier.strip("/")
        for trans in self.transforms:
            if trans.scope.strip("/").startswith(norm):
                return True
        return False
    
    # -------------------------------------------------------------------------
    # Outputs API
    # -------------------------------------------------------------------------
    
    def get_outputs(self, scope: Optional[str] = None) -> Any:
        """Get outputs, optionally filtered by scope.
        
        Args:
            scope: If provided, return the attributes dict for the output
                   with this scope. If None, return list of all output scopes.
        
        Returns:
            - If scope is None: List of scope strings for all outputs.
            - If scope is provided: Dictionary of attributes for that output,
              or None if no output matches the scope.
        """
        if scope is None:
            return [o.scope for o in self.outputs]
        
        for out in self.outputs:
            if out.scope == scope:
                return out.to_dict()
        return None
    
    def has_output(self, identifier: str) -> bool:
        """Return True if any output's scope starts with identifier."""
        if not identifier:
            return False
        norm = identifier.strip("/")
        for out in self.outputs:
            if out.scope.strip("/").startswith(norm):
                return True
        return False
    
    # -------------------------------------------------------------------------
    # YAML Loading
    # -------------------------------------------------------------------------
    
    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> "Process":
        """Deserialize a Process from YAML-loaded dict.
        
        Expected structure matches domain_processes.template.yaml.
        """
        path = data.get("path", "")
        name = data.get("name", "")
        
        # Parse time block
        time_spec = data.get("time", {})
        base_duration = float(time_spec.get("base_duration", 0.0))
        by_material = {}
        for mat_path, dur in time_spec.get("by_material", {}).items():
            by_material[mat_path] = float(dur)
        
        # Parse requirements
        requirements = []
        for req_data in data.get("requirements", []) or []:
            req = Requirement(
                name=req_data.get("name", ""),
                scope=req_data.get("scope", ""),
                material=req_data.get("material"),
                quantity=float(req_data.get("quantity", 1)),
                properties=req_data.get("properties", []),
                mtbf=req_data.get("mtbf"),
            )
            requirements.append(req)
        
        # Parse inputs
        inputs = []
        for inp_data in data.get("inputs", []) or []:
            inp = Input(
                name=inp_data.get("name", ""),
                scope=inp_data.get("scope", ""),
                material=inp_data.get("material"),
                quantity=float(inp_data.get("quantity", 1)),
                properties=inp_data.get("properties", []),
            )
            inputs.append(inp)
        
        # Parse transforms
        transforms = []
        for trans_data in data.get("transforms", []) or []:
            trans = Transform(
                name=trans_data.get("name", ""),
                scope=trans_data.get("scope", ""),
                material=trans_data.get("material"),
                quantity=float(trans_data.get("quantity", 1)),
                properties=trans_data.get("properties", []),
                add_properties=trans_data.get("add_properties", []),
                remove_properties=trans_data.get("remove_properties", []),
                new_scope=trans_data.get("new_scope"),
                new_material=trans_data.get("new_material"),
            )
            transforms.append(trans)
        
        # Parse outputs
        outputs = []
        for out_data in data.get("outputs", []) or []:
            out = Output(
                name=out_data.get("name", ""),
                scope=out_data.get("scope", ""),
                material=out_data.get("material"),
                quantity=float(out_data.get("quantity", 1)),
                properties=out_data.get("properties", []),
            )
            outputs.append(out)
        
        return cls(
            path=path,
            name=name,
            base_duration=base_duration,
            by_material=by_material,
            requirements=requirements,
            inputs=inputs,
            transforms=transforms,
            outputs=outputs,
        )
    
    def __repr__(self) -> str:
        return (
            f"Process(path={self.path!r}, name={self.name!r}, "
            f"duration={self.base_duration}h, "
            f"reqs={len(self.requirements)}, inputs={len(self.inputs)}, "
            f"transforms={len(self.transforms)}, outputs={len(self.outputs)})"
        )
