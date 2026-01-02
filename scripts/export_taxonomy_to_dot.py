"""Export Demesne domain `scopes` to a Graphviz DOT file.

Usage:
  python3 scripts/export_taxonomy_to_dot.py \
      --input simulations/Demesne/domain.yaml \
      --output simulations/Demesne/demesne_taxonomy.dot

Render with Graphviz:
  dot -Tpng -O simulations/Demesne/demesne_taxonomy.dot

The script creates a node per scope path component and edges parent->child.
"""
from pathlib import Path
import argparse
import yaml


def safe_id(path: str) -> str:
    return "n_" + path.replace("/", "__").replace("-", "_").replace(" ", "_")


def load_paths(yaml_path: Path):
    data = yaml.safe_load(yaml_path.read_text())
    scopes = data.get("scopes") or []
    paths = []
    for item in scopes:
        if isinstance(item, dict) and "path" in item:
            paths.append(str(item["path"]))
        elif isinstance(item, str):
            paths.append(item)
    return paths


def build_graph(paths):
    nodes = set()
    edges = set()
    for path in paths:
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            continue
        for i in range(len(parts)):
            node = "/".join(parts[: i + 1])
            nodes.add(node)
        for i in range(len(parts) - 1):
            parent = "/".join(parts[: i + 1])
            child = "/".join(parts[: i + 2])
            edges.add((parent, child))
    return nodes, edges


def write_dot(nodes, edges, out_path: Path, graph_name="DemesneTaxonomy"):
    lines = []
    lines.append(f"digraph {graph_name} {{")
    lines.append('  graph [rankdir="TB", fontsize=10];')
    lines.append('  node [shape=box, fontsize=9];')

    for n in sorted(nodes):
        nid = safe_id(n)
        label = n.split("/")[-1]
        lines.append(f'  {nid} [label="{label}\\n({n})"];')

    for parent, child in sorted(edges):
        lines.append(f'  {safe_id(parent)} -> {safe_id(child)};')

    lines.append("}")
    out_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Export domain scopes to Graphviz DOT")
    parser.add_argument("--input", "-i", default="simulations/Demesne/domain.yaml",
                        help="path to domain YAML (default: simulations/Demesne/domain.yaml)")
    parser.add_argument("--output", "-o", default="simulations/Demesne/demesne_taxonomy.dot",
                        help="output .dot file (default: simulations/Demesne/demesne_taxonomy.dot)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)

    if not inp.exists():
        print(f"Error: input file not found: {inp}")
        raise SystemExit(2)

    try:
        paths = load_paths(inp)
    except Exception as e:
        print(f"Error loading YAML from {inp}: {e}")
        raise

    nodes, edges = build_graph(paths)

    # ensure output directory exists
    if not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)

    write_dot(nodes, edges, out)
    print(f"Wrote {out} ({len(nodes)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    main()
