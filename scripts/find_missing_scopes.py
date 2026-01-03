#!/usr/bin/env python3
"""
Scan a domain YAML (`domain.yaml`) and a processes YAML (`domain_processes.yaml`)
and report taxonomy-like identifiers referenced by the processes file that are
not declared in the domain's `scopes` list.

Usage:
  python3 scripts/find_missing_scopes.py -d simulations/Demesne/domain.yaml \
    -p simulations/Demesne/domain_processes.yaml

"""
from pathlib import Path
import argparse
import yaml
import re
from typing import Set, Any

SCOPE_RE = re.compile(r"^[a-z][a-z0-9_\-]*/[a-z0-9_\-/]+$", re.IGNORECASE)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def gather_domain_scopes(domain_data) -> Set[str]:
    scopes = set()
    for entry in domain_data.get("scopes", []) or []:
        if isinstance(entry, dict) and "path" in entry:
            scopes.add(str(entry["path"]).strip("/"))
        elif isinstance(entry, str):
            scopes.add(entry.strip("/"))
    return scopes


def gather_strings(obj) -> Set[str]:
    found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            # include keys that look like items/paths too
            if isinstance(k, str) and SCOPE_RE.match(k.strip()):
                found.add(k.strip("/"))
            found |= gather_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            found |= gather_strings(item)
    elif isinstance(obj, str):
        s = obj.strip()
        if SCOPE_RE.match(s):
            found.add(s.strip("/"))
    return found


def gather_process_references(processes_data) -> Set[str]:
    refs = set()
    # processes_data expected to be a dict with `processes` list
    for p in processes_data.get("processes", []) or []:
        refs |= gather_strings(p)
    return refs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", "-d", required=True)
    p.add_argument("--processes", "-p", required=True)
    args = p.parse_args()

    domain_path = Path(args.domain)
    proc_path = Path(args.processes)

    if not domain_path.exists():
        print(f"Domain file not found: {domain_path}")
        raise SystemExit(2)
    if not proc_path.exists():
        print(f"Processes file not found: {proc_path}")
        raise SystemExit(2)

    domain_data = load_yaml(domain_path)
    processes_data = load_yaml(proc_path)

    domain_scopes = gather_domain_scopes(domain_data)
    process_refs = gather_process_references(processes_data)

    # Filter to strings that look like taxonomy paths (have at least one '/')
    process_refs = {r for r in process_refs if "/" in r}

    missing = sorted(process_refs - domain_scopes)
    unused = sorted(domain_scopes - process_refs)

    print(f"Domain scopes: {len(domain_scopes)}")
    print(f"Process-referenced scope-like strings: {len(process_refs)}")
    print()
    if missing:
        print("Scopes referenced in processes but MISSING from domain.yaml:")
        for m in missing:
            print("  -", m)
    else:
        print("No missing scopes referenced by processes.")
    print()
    print("Domain scopes NOT referenced by processes (sample up to 40):")
    for u in unused[:40]:
        print("  -", u)


if __name__ == "__main__":
    main()
