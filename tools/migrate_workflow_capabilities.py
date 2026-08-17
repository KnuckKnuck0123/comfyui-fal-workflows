#!/usr/bin/env python
"""Migrate Fal workflow JSON graphs from the legacy flat node to typed nodes."""

from __future__ import annotations

import json
from pathlib import Path

from tools.update_fal_catalog import (
    DEFAULT_OUTPUT,
    NODE_TYPE_CATEGORIES,
    ROOT,
    CatalogError,
    node_type_for_endpoint,
)


def migrate_api(graph: dict, catalog: dict) -> int:
    changed = 0
    for node in graph.values():
        endpoint = node.get("inputs", {}).get("endpoint")
        if node.get("class_type") == "FalGenericAPI" and isinstance(endpoint, str):
            node["class_type"] = node_type_for_endpoint(catalog, endpoint)
            changed += 1
    return changed


def migrate_gui(graph: dict, catalog: dict) -> int:
    changed = 0
    for node in graph.get("nodes", []):
        widgets = node.get("widgets_values", [])
        endpoint = widgets[0] if widgets and isinstance(widgets[0], str) else None
        if node.get("type") == "FalGenericAPI" and endpoint:
            node_type = node_type_for_endpoint(catalog, endpoint)
            node["type"] = node_type
            node.setdefault("properties", {})["Node name for S&R"] = node_type
            changed += 1
    return changed


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_registry(catalog: dict) -> tuple[int, int]:
    path = ROOT / "fal_models.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    metadata_changes = 0
    removed_values = 0
    for metadata in registry.get("workflows", {}).values():
        graph_path = ROOT / "workflows_api" / metadata.get("file", "")
        if not graph_path.is_file():
            continue
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        typed_nodes = {
            node.get("class_type")
            for node in graph.values()
            if node.get("class_type") in NODE_TYPE_CATEGORIES
        }
        if not typed_nodes:
            continue
        engine_node = metadata.get("engine_node", "")
        if "FalGenericAPI" in engine_node and len(typed_nodes) == 1:
            metadata["engine_node"] = engine_node.replace("FalGenericAPI", next(iter(typed_nodes)))
            metadata_changes += 1
        values = metadata.get("swappable_values")
        if not isinstance(values, list):
            continue
        allowed_categories = {
            category for node_type in typed_nodes for category in NODE_TYPE_CATEGORIES[node_type]
        }
        kept = [
            endpoint for endpoint in values
            if catalog.get("models", {}).get(endpoint, {}).get("category") in allowed_categories
        ]
        if kept != values:
            removed_values += len(values) - len(kept)
            metadata["swappable_values"] = kept
    write_json(path, registry)
    return metadata_changes, removed_values


def main() -> int:
    catalog = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    total = 0
    for path in sorted((ROOT / "workflows_api").glob("*.json")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        changed = migrate_api(graph, catalog)
        if changed:
            write_json(path, graph)
            print(f"API {path.name}: {changed}")
            total += changed
    for path in sorted((ROOT / "workflows_gui").glob("*.json")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        changed = migrate_gui(graph, catalog)
        if changed:
            write_json(path, graph)
            print(f"GUI {path.name}: {changed}")
            total += changed
    metadata_changes, removed_values = migrate_registry(catalog)
    print(f"Registry metadata updated: {metadata_changes}; incompatible swap values removed: {removed_values}")
    print(f"Migrated {total} legacy Fal nodes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CatalogError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
