#!/usr/bin/env python
"""Refresh, validate, report, and optionally deploy Fal capability metadata.

Official contract:
https://api.fal.ai/v1/openapi.json (GET /models, operationId=getModels)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "catalog" / "fal_endpoint_catalog.json"
API_URL = "https://api.fal.ai/v1/models"
SUPPORTED_CATEGORIES = (
    "text-to-image",
    "image-to-image",
    "text-to-video",
    "image-to-video",
    "video-to-video",
    "audio-to-video",
    "text-to-3d",
    "image-to-3d",
    "3d-to-3d",
)
NODE_TYPE_CATEGORIES = {
    "FalTextToImageAPI": ("text-to-image",),
    "FalImageToImageAPI": ("image-to-image",),
    "FalImageUpscaleAPI": ("image-to-image",),
    "FalTextToVideoAPI": ("text-to-video",),
    "FalImageToVideoAPI": ("image-to-video",),
    "FalVideoToVideoAPI": ("video-to-video",),
    "FalAudioToVideoAPI": ("audio-to-video",),
    "FalTextTo3DAPI": ("text-to-3d",),
    "FalImageTo3DAPI": ("image-to-3d",),
    "Fal3DTo3DAPI": ("3d-to-3d",),
}
CATEGORY_NODE_TYPES = {
    category: node_type
    for node_type, categories in NODE_TYPE_CATEGORIES.items()
    if node_type != "FalImageUpscaleAPI"
    for category in categories
}


class CatalogError(ValueError):
    """Raised when Fal returns data outside the documented models contract."""


def _validate_model(value: object) -> dict:
    if not isinstance(value, dict):
        raise CatalogError("Every model must be an object")
    endpoint_id = value.get("endpoint_id")
    metadata = value.get("metadata")
    if not isinstance(endpoint_id, str) or not endpoint_id.strip():
        raise CatalogError("Every model needs a non-empty endpoint_id")
    if not isinstance(metadata, dict):
        raise CatalogError(f"{endpoint_id}: metadata must be an object")
    for field in ("category", "display_name", "status"):
        if not isinstance(metadata.get(field), str):
            raise CatalogError(f"{endpoint_id}: metadata.{field} must be a string")
    tags = metadata.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise CatalogError(f"{endpoint_id}: metadata.tags must be a string list")
    return value


def collect_models(fetch_page: Callable[[str | None], object]) -> list[dict]:
    """Collect all pages through the documented cursor contract."""
    cursor = None
    seen_cursors: set[str] = set()
    by_id: dict[str, dict] = {}
    while True:
        page = fetch_page(cursor)
        if not isinstance(page, dict) or not isinstance(page.get("models"), list):
            raise CatalogError("Fal response models must be a list")
        for raw_model in page["models"]:
            item = _validate_model(raw_model)
            by_id[item["endpoint_id"]] = item
        has_more = page.get("has_more", False)
        if not isinstance(has_more, bool):
            raise CatalogError("Fal response has_more must be a boolean")
        if not has_more:
            break
        next_cursor = page.get("next_cursor")
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
            raise CatalogError("Fal pagination requires a new non-empty next_cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return [by_id[key] for key in sorted(by_id, key=str.casefold)]


def request_headers(environment: dict[str, str] | os._Environ[str]) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    key = environment.get("FAL_KEY")
    if key:
        headers["Authorization"] = f"Key {key}"
    return headers


def fetch_page(cursor: str | None) -> dict:
    params = {"limit": 100, "status": "active"}
    if cursor:
        params["cursor"] = cursor
    request = Request(f"{API_URL}?{urlencode(params)}", headers=request_headers(os.environ))
    with urlopen(request, timeout=45) as response:
        return json.load(response)


def _is_upscaler(endpoint_id: str, metadata: dict) -> bool:
    haystack = " ".join(
        [endpoint_id, metadata.get("display_name", ""), metadata.get("description", ""), *metadata.get("tags", [])]
    ).casefold()
    return any(token in haystack for token in ("upscale", "upscaler", "super-resolution", "super resolution"))


def build_catalog(models: list[dict], *, generated_at: str | None = None) -> dict:
    categories = {category: [] for category in SUPPORTED_CATEGORIES}
    records: dict[str, dict] = {}
    image_upscale: list[str] = []
    for raw_model in models:
        item = _validate_model(raw_model)
        endpoint_id = item["endpoint_id"]
        metadata = item["metadata"]
        if metadata["status"] != "active" or metadata["category"] not in categories:
            continue
        categories[metadata["category"]].append(endpoint_id)
        if metadata["category"] == "image-to-image" and _is_upscaler(endpoint_id, metadata):
            image_upscale.append(endpoint_id)
        records[endpoint_id] = {
            "display_name": metadata["display_name"],
            "category": metadata["category"],
            "status": metadata["status"],
            "date": metadata.get("date"),
            "updated_at": metadata.get("updated_at"),
            "tags": metadata.get("tags", []),
        }
    for endpoints in categories.values():
        endpoints.sort(key=str.casefold)
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "source": API_URL,
        "generated_at": timestamp,
        "categories": categories,
        "roles": {"image-upscale": sorted(image_upscale, key=str.casefold)},
        "models": {key: records[key] for key in sorted(records, key=str.casefold)},
    }


def node_type_for_endpoint(catalog: dict, endpoint_id: str) -> str:
    models = catalog.get("models", {})
    if not isinstance(models, dict) or endpoint_id not in models:
        raise CatalogError(f"Endpoint is not present in the active catalog: {endpoint_id}")
    roles = catalog.get("roles", {})
    if isinstance(roles, dict) and endpoint_id in roles.get("image-upscale", []):
        return "FalImageUpscaleAPI"
    category = models[endpoint_id].get("category")
    try:
        return CATEGORY_NODE_TYPES[category]
    except KeyError as exc:
        raise CatalogError(f"No typed node is defined for category {category!r}") from exc


def _load_existing(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Cannot read existing catalog {path}: {exc}") from exc
    return value if isinstance(value, dict) else None


def _endpoint_set(catalog: dict | None) -> set[str]:
    models = catalog.get("models", {}) if catalog else {}
    return set(models) if isinstance(models, dict) else set()


def write_catalog(path: Path, catalog: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def deploy(node_root: Path, catalog_path: Path) -> None:
    node_root = node_root.resolve()
    init_path = node_root / "__init__.py"
    nodes_dir = node_root / "nodes"
    if not init_path.is_file() or not (nodes_dir / "generic_node.py").is_file():
        raise CatalogError(f"Not a ComfyUI-fal-API node root: {node_root}")
    for name in (
        "capability_catalog.py",
        "capability_node.py",
        "endpoint_image_arguments.py",
        "endpoint_result_url.py",
    ):
        shutil.copy2(ROOT / "comfyui_nodes" / name, nodes_dir / name)
    shutil.copy2(catalog_path, nodes_dir / "fal_endpoint_catalog.json")
    source = init_path.read_text(encoding="utf-8")
    if '"capability_node"' not in source:
        marker = '    "generic_node",\n'
        if marker not in source:
            raise CatalogError(f"Cannot locate generic_node registration in {init_path}")
        init_path.write_text(source.replace(marker, marker + '    "capability_node",\n'), encoding="utf-8")


def deploy_workflows(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted((ROOT / "workflows_gui").glob("*.json")):
        shutil.copy2(source, destination / source.name)
        count += 1
    return count


def print_report(old: dict | None, new: dict, *, verbose: bool = False) -> None:
    added = sorted(_endpoint_set(new) - _endpoint_set(old), key=str.casefold)
    removed = sorted(_endpoint_set(old) - _endpoint_set(new), key=str.casefold)
    print(f"Cataloged {len(new['models'])} active endpoints across {len(SUPPORTED_CATEGORIES)} capabilities.")
    print(f"Added: {len(added)}; removed/inactive: {len(removed)}")
    added_set = set(added)
    removed_set = set(removed)
    for category in SUPPORTED_CATEGORIES:
        current = new["categories"].get(category, [])
        old_category = (old or {}).get("categories", {}).get(category, [])
        added_count = len(set(current) & added_set)
        removed_count = len(set(old_category) & removed_set)
        print(f"  {category:<16} {len(current):>4} active  +{added_count} / -{removed_count}")
    if not verbose:
        if added or removed:
            print("Use --verbose to list individual endpoint changes.")
        return
    for label, endpoints in (("NEW", added), ("REMOVED", removed)):
        for endpoint in endpoints:
            metadata = new["models"].get(endpoint) or (old or {}).get("models", {}).get(endpoint, {})
            print(f"  {label:<7} {metadata.get('category', '?'):<16} {endpoint}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--deploy-node-root", type=Path, help="Copy the catalog and typed nodes into ComfyUI-fal-API")
    parser.add_argument("--deploy-workflows-dir", type=Path, help="Copy GUI workflows into ComfyUI Desktop")
    parser.add_argument("--verbose", action="store_true", help="List every added and removed endpoint")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        old = _load_existing(args.output)
        models = collect_models(fetch_page)
        catalog = build_catalog(models)
        write_catalog(args.output, catalog)
        print_report(old, catalog, verbose=args.verbose)
        if args.deploy_node_root:
            deploy(args.deploy_node_root, args.output)
            print(f"Deployed capability nodes to {args.deploy_node_root.resolve()}")
        if args.deploy_workflows_dir:
            count = deploy_workflows(args.deploy_workflows_dir)
            print(f"Deployed {count} GUI workflows to {args.deploy_workflows_dir.resolve()}")
    except (CatalogError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
