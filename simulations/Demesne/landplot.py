from dataclasses import dataclass, field
from typing import Optional

from simframework.entity import Entity
from simframework.scope import Scope


@dataclass
class LandPlot(Entity):
    """A land plot in the Demesne simulation.

    Attributes:
        stage: Optional[Scope] - the taxonomic scope describing the plant growth stage
        vegetation: Optional[Scope] - the taxonomic scope specifying what's growing
        acreage: float - area of the plot in acres (non-negative)
    """
    essence: Scope = field(default=Scope(name="land/plot/arable"), init=False)
    stage: Optional[Scope] = None
    vegetation: Optional[Scope] = None
    acreage: float = 0.0

    def __post_init__(self) -> None:
        # Validate base Entity fields
        super().__post_init__()

        if self.stage is not None and not isinstance(self.stage, Scope):
            raise TypeError("stage must be a simframework.scope.Scope or None")
        if self.vegetation is not None and not isinstance(self.vegetation, Scope):
            raise TypeError("vegetation must be a simframework.scope.Scope or None")
        if not isinstance(self.acreage, (int, float)) or self.acreage < 0:
            raise ValueError("acreage must be a non-negative number")

    # Getter and setter methods for stage, vegetation, and acreage
    
    def set_stage(self, scope: Optional[Scope]) -> None:
        """Set the growth stage scope for this landplot."""
        if scope is not None and not isinstance(scope, Scope):
            raise TypeError("scope must be a Scope or None")
        self.stage = scope

    def set_vegetation(self, scope: Optional[Scope]) -> None:
        """Set the vegetation scope for this landplot."""
        if scope is not None and not isinstance(scope, Scope):
            raise TypeError("scope must be a Scope or None")
        self.vegetation = scope

    def get_vegetation(self) -> Optional[Scope]:
        """Return the vegetation scope for this landplot."""
        return self.vegetation

    def get_stage(self) -> Optional[Scope]:
        """Return the growth stage scope for this landplot."""
        return self.stage
    
    def get_acreage(self) -> float:
        """Return the acreage of this landplot."""
        return self.acreage
    
    def set_acreage(self, acreage: float) -> None:
        """Set the acreage of this landplot."""
        if not isinstance(acreage, (int, float)) or acreage < 0:
            raise ValueError("acreage must be a non-negative number")
        self.acreage = acreage

