"""simframework package entry point"""

__all__ = ["Scheduler", "SimulationEngine", "Entity", "Event", "Scope", "Domain", "SystemTemplate", "SystemInstance"]

try:
	# Prefer absolute imports when package is installed or run as a module
	from simframework.scheduler import Scheduler
	from simframework.engine import SimulationEngine
	from simframework.entity import Entity
	from simframework.event import Event
	from simframework.scope import Scope, Domain
	from simframework.system import SystemTemplate, SystemInstance
except Exception:
	# Fallback to relative imports (useful when running files directly)
	from .scheduler import Scheduler
	from .engine import SimulationEngine
	from .entity import Entity
	from .event import Event
	from .scope import Scope, Domain
	from .system import SystemTemplate, SystemInstance

__version__ = "0.1.0"
