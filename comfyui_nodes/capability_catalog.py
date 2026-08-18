"""Load endpoint choices from a validated Fal model-catalog snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class CapabilityCatalogError(ValueError):
    """Raised when a local catalog snapshot does not match the expected contract."""


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise CapabilityCatalogError(f"{field} must be a list of non-empty strings")
    return value


def load_endpoint_choices(
    path: Path,
    *,
    categories: Iterable[str] = (),
    role: str | None = None,
) -> list[str]:
    """Return sorted endpoint IDs for exact Fal categories or one derived role."""
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityCatalogError(f"Cannot read Fal endpoint catalog: {exc}") from exc

    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise CapabilityCatalogError("Unsupported Fal endpoint catalog schema")

    selected: set[str] = set()
    category_map = catalog.get("categories")
    if not isinstance(category_map, dict):
        raise CapabilityCatalogError("categories must be an object")
    for category in categories:
        selected.update(_string_list(category_map.get(category, []), f"categories.{category}"))

    if role is not None:
        role_map = catalog.get("roles")
        if not isinstance(role_map, dict):
            raise CapabilityCatalogError("roles must be an object")
        selected.update(_string_list(role_map.get(role, []), f"roles.{role}"))

    return sorted(selected, key=str.casefold)
