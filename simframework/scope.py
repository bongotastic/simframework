"""Scope and Domain classes for hierarchical categorization in simulations.

A Scope represents a category in a hierarchy with optional metadata.
A Domain is a collection of related Scopes that define the structure
for a particular simulation framework.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class Scope:
    """A scope representing a category in a taxonomy.

    A scope can have a parent scope, creating a hierarchy. Scopes can also
    carry metadata via properties for domain-specific information.
    """

    name: str
    parent: Optional[Scope] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def full_path(self) -> str:
        """Return the full hierarchical path of this scope (e.g., 'biology/organism/growth')."""
        if self.parent is None:
            return self.name
        return f"{self.parent.full_path()}/{self.name}"

    def ancestors(self) -> List[Scope]:
        """Return list of ancestor scopes, from root to parent."""
        if self.parent is None:
            return []
        return self.parent.ancestors() + [self.parent]

    def is_ancestor_of(self, other: Scope) -> bool:
        """Check if this scope is an ancestor of another scope."""
        current = other.parent
        while current is not None:
            if current is self:
                return True
            current = current.parent
        return False

    def depth(self) -> int:
        """Return the depth of this scope in the hierarchy (root = 0)."""
        if self.parent is None:
            return 0
        return 1 + self.parent.depth()

    def __repr__(self) -> str:
        return f"Scope(path='{self.full_path()}', properties={self.properties})"

    def __eq__(self, other: Any) -> bool:
        """Two scopes are equal if they have the same full path."""
        if not isinstance(other, Scope):
            return False
        return self.full_path() == other.full_path()

    def __hash__(self) -> int:
        """Hash based on full path for use in sets/dicts."""
        return hash(self.full_path())


class Domain:
    """A domain defines all scopes for a particular simulation framework.

    A domain acts as a registry of scopes, allowing structured access,
    filtering, and querying by hierarchy.
    """

    def __init__(self, name: str):
        """Initialize a domain with a name.

        Args:
            name: The name of this domain (e.g., 'EcologicalSimulation').
        """
        self.name = name
        self._scopes: Dict[str, Scope] = {}
        # Template registries for systems and agents (populated from YAML)
        from .system import SystemTemplate, AgentTemplate  # local import to avoid top-level cycle
        self.system_templates: Dict[str, SystemTemplate] = {}
        self.agent_templates: Dict[str, AgentTemplate] = {}

    def get_system_template(self, name: str) -> Optional["SystemTemplate"]:
        return self.system_templates.get(name)

    def get_agent_template(self, name: str) -> Optional["AgentTemplate"]:
        return self.agent_templates.get(name)

    def register_scope(self, scope: Scope) -> None:
        """Register a scope in this domain.

        Args:
            scope: The Scope to register.

        Raises:
            ValueError: If a scope with the same full path is already registered.
        """
        path = scope.full_path()
        if path in self._scopes:
            raise ValueError(f"Scope '{path}' is already registered in domain '{self.name}'")
        self._scopes[path] = scope

    def get_scope(self, full_path: str) -> Optional[Scope]:
        """Retrieve a scope by its full hierarchical path.

        Args:
            full_path: The full path (e.g., 'biology/organism/growth').

        Returns:
            The Scope if found, None otherwise.
        """
        return self._scopes.get(full_path)

    def get_scopes_by_ancestor(self, ancestor: Scope) -> List[Scope]:
        """Get all scopes that have a specific ancestor (or are equal to it).

        Args:
            ancestor: The ancestor Scope to filter by.

        Returns:
            A list of Scopes that have the ancestor in their hierarchy.
        """
        result = [ancestor]
        for scope in self._scopes.values():
            if ancestor.is_ancestor_of(scope):
                result.append(scope)
        return result

    def list_all_scopes(self) -> List[Scope]:
        """Return all registered scopes in this domain."""
        return list(self._scopes.values())

    def scopes_at_depth(self, depth: int) -> List[Scope]:
        """Return all scopes at a specific depth in the hierarchy."""
        return [scope for scope in self._scopes.values() if scope.depth() == depth]

    def __repr__(self) -> str:
        scope_count = len(self._scopes)
        return f"Domain(name='{self.name}', scopes={scope_count})"

    @classmethod
    def from_yaml(cls, filepath: str) -> "Domain":
        """Load a Domain definition from a YAML file or directory of YAML files.

        If `filepath` is a directory, all files ending with `.yaml` or `.yml`
        in that directory are loaded in alphabetical order and merged into a
        single Domain. Later files may add additional scopes.

        The YAML format expected for each file is:

        name: Optional domain name
        scopes:
          - path: "root/child/sub"
            properties:
              key: value

        Each `path` is split on `/` to create any necessary parent scopes.
        """
        try:
            import yaml
        except Exception as exc:  # pragma: no cover - dependency/platform
            raise RuntimeError("PyYAML is required to load domain YAML") from exc

        from pathlib import Path
        p = Path(filepath)

        # Support glob patterns (e.g., 'simulations/**/*.yaml')
        pattern_chars = set("*?[]")
        is_glob = any((c in filepath) for c in pattern_chars) or "**" in filepath

        files: List[Path] = []
        if is_glob:
            # Use glob.glob which supports absolute and recursive patterns
            import glob as _glob
            matched = sorted(_glob.glob(filepath, recursive=True))
            for m in matched:
                f = Path(m)
                if f.suffix.lower() in (".yml", ".yaml") and f.is_file():
                    files.append(f)
            if not files:
                raise FileNotFoundError(f"No YAML files matched glob: {filepath}")
        else:
            if not p.exists():
                raise FileNotFoundError(f"Domain YAML path not found: {filepath}")

            if p.is_dir():
                # Collect YAML files sorted for deterministic loading order
                for child in sorted(p.iterdir()):
                    if child.suffix.lower() in (".yml", ".yaml") and child.is_file():
                        files.append(child)
            else:
                files = [p]

        domain = None
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}

            name = data.get("name")
            if domain is None:
                domain = cls(name or "domain")
            # If multiple files provide a name, we keep the first non-empty name.

            # --- parse scopes as before ---
            for entry in data.get("scopes", []) or []:
                path = entry.get("path") or entry.get("name")
                if not path:
                    continue
                properties = entry.get("properties", {}) or {}
                parts = [p for p in path.split("/") if p]
                parent = None
                for i, part in enumerate(parts):
                    full = "/".join(parts[: i + 1])
                    existing = domain.get_scope(full)
                    if existing is None:
                        props = properties if i == len(parts) - 1 else {}
                        scope = Scope(name=part, parent=parent, properties=props)
                        domain.register_scope(scope)
                        parent = scope
                    else:
                        parent = existing

            # --- new: parse system and agent templates ---
            # Import templates here to avoid circular imports at module load time
            from .system import SystemTemplate, AgentTemplate

            def _build_template(entry: dict, agent: bool = False):
                tmpl_cls = AgentTemplate if agent else SystemTemplate
                name = entry.get("name") or entry.get("id")
                if name is None:
                    raise ValueError("template entry missing 'name' or 'id'")
                props = entry.get("properties", {}) or {}
                children = []
                for child in entry.get("children", []) or []:
                    child_is_agent = isinstance(child, dict) and child.get("type") == "agent"
                    children.append(_build_template(child, agent=child_is_agent))
                tmpl = tmpl_cls(name, properties=props)
                for c in children:
                    tmpl.add_child(c)
                return tmpl

            # Systems
            for entry in data.get("systems", []) or []:
                tmpl = _build_template(entry, agent=False)
                domain.system_templates[tmpl.name] = tmpl

            # Agents
            for entry in data.get("agents", []) or []:
                tmpl = _build_template(entry, agent=True)
                domain.agent_templates[tmpl.name] = tmpl

        if domain is None:
            # No files matched; return an empty domain with the directory name
            return cls(Path(filepath).name)

        return domain
