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

    A scope can have a parent scope and children scopes, creating a tree hierarchy.
    Scopes can also carry metadata via properties for domain-specific information.
    """

    name: str
    parent: Optional[Scope] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    children: Set[Scope] = field(default_factory=set)

    def add_child(self, child: "Scope") -> None:
        """Add a child scope to this scope's children set."""
        self.children.add(child)

    def get_children(self) -> List["Scope"]:
        """Return a sorted list of child scopes by name."""
        return sorted(self.children, key=lambda s: s.name)

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
        # Represent a scope by its full taxonomic path
        return self.full_path()

    def __eq__(self, other: Any) -> bool:
        """Two scopes are equal if they have the same full path."""
        if not isinstance(other, Scope):
            return False
        return self.full_path() == other.full_path()

    def __hash__(self) -> int:
        """Hash based on full path for use in sets/dicts."""
        return hash(self.full_path())


class Domain:
    """A domain defines a taxonomy of scopes and processes for a simulation.

    The Domain holds:
    - taxonomy: A tree of hierarchical scopes from domain.yaml
    - processes: A dict of process definitions from domain_processes.yaml
    """

    def __init__(self, name: str):
        """Initialize a domain with a name.

        Args:
            name: The name of this domain (e.g., 'EcologicalSimulation').
        """
        self.name = name
        self.taxonomy: Dict[str, Scope] = {}  # full_path -> Scope
        self.processes: Dict[str, Dict[str, Any]] = {}  # process_path -> process_dict

    def register_scope(self, scope: Scope) -> None:
        """Register a scope in this domain.

        Args:
            scope: The Scope to register.

        Raises:
            ValueError: If a scope with the same full path is already registered.
        """
        path = scope.full_path()
        if path in self.taxonomy:
            raise ValueError(f"Scope '{path}' is already registered in domain '{self.name}'")
        self.taxonomy[path] = scope
        # Ensure parent tracks this scope as a child
        if scope.parent is not None:
            scope.parent.add_child(scope)

    def get_scope(self, full_path: str) -> Optional[Scope]:
        """Retrieve a scope by its full hierarchical path.

        Args:
            full_path: The full path (e.g., 'biology/organism/growth').

        Returns:
            The Scope if found, None otherwise.
        """
        return self.taxonomy.get(full_path)

    def get_scopes_by_ancestor(self, ancestor: Scope) -> List[Scope]:
        """Get all scopes that have a specific ancestor (or are equal to it).

        Args:
            ancestor: The ancestor Scope to filter by.

        Returns:
            A list of Scopes that have the ancestor in their hierarchy.
        """
        result = [ancestor]
        for scope in self.taxonomy.values():
            if ancestor.is_ancestor_of(scope):
                result.append(scope)
        return result

    def query_by_name(self, name: str) -> List[Scope]:
        """Find all scopes that have the given name anywhere in their path.

        Args:
            name: The scope name to search for (e.g., 'crop').

        Returns:
            A list of Scopes whose full path contains the given name as a path component.
        """
        result = []
        for scope in self.taxonomy.values():
            if name in scope.full_path().split('/'):
                result.append(scope)
        return result

    def list_all_scopes(self) -> List[Scope]:
        """Return all registered scopes in this domain."""
        return list(self.taxonomy.values())

    def scopes_at_depth(self, depth: int) -> List[Scope]:
        """Return all scopes at a specific depth in the hierarchy."""
        return [scope for scope in self.taxonomy.values() if scope.depth() == depth]

    def register_process(self, process_path: str, process_data: Dict[str, Any]) -> None:
        """Register a process definition in this domain.

        Args:
            process_path: The unique path of the process (e.g., 'process/production/forging').
            process_data: The process definition dict from YAML.
        """
        self.processes[process_path] = process_data

    def get_process(self, process_path: str) -> Optional[Dict[str, Any]]:
        """Retrieve a process definition by its path.

        Args:
            process_path: The full path of the process.

        Returns:
            The process definition dict if found, None otherwise.
        """
        return self.processes.get(process_path)

    def __repr__(self) -> str:
        scope_count = len(self.taxonomy)
        process_count = len(self.processes)
        return f"Domain(name='{self.name}', scopes={scope_count}, processes={process_count})"

    @classmethod
    def from_yaml(cls, filepath: str) -> "Domain":
        """Load a Domain definition from a YAML file or directory of YAML files.

        If `filepath` is a directory, all files ending with `.yaml` or `.yml`
        in that directory are loaded in alphabetical order and merged into a
        single Domain. Later files may add additional scopes and processes.

        Domain files (domain.yaml) define scopes:

        name: Optional domain name
        scopes:
          - path: "root/child/sub"
            properties:
              key: value

        Process files (domain_processes.yaml) define processes:

        name: Optional process collection name
        processes:
          - path: "process/production/example"
            name: "Example Process"
            type: manual
            time:
              base_duration: 2.0
            requirements: {...}
            inputs: {...}
            outputs: {...}

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

            # --- Parse scopes from domain.yaml ---
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

            # --- Parse processes from domain_processes.yaml ---
            for entry in data.get("processes", []) or []:
                process_path = entry.get("path")
                if not process_path:
                    continue
                # Store the entire process definition
                domain.register_process(process_path, entry)


        if domain is None:
            # No files matched; return an empty domain with the directory name
            return cls(Path(filepath).name)

        return domain
