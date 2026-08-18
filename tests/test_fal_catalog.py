import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


SAMPLE_MODELS = [
    ("meshy/v7/image-to-3d", "image-to-3d", "Meshy V7 Image to 3D"),
    ("hitem3d/hi3d/texture", "3d-to-3d", "Hi3D Texture"),
    ("lightricks/ltx-2.5/text-to-video/pro", "text-to-video", "LTX 2.5 Pro"),
    ("minimax/h3/image-to-video", "image-to-video", "MiniMax H3"),
    ("bytedance/seedream/v5/pro/edit", "image-to-image", "Seedream 5 Pro Edit"),
    ("blackforestlabs/flux-3/extend-video", "video-to-video", "FLUX 3 Extend"),
    ("fal-ai/flux-2", "text-to-image", "FLUX 2"),
    ("fal-ai/topaz/upscale/image", "image-to-image", "Topaz Upscale"),
]


def model(endpoint_id, category, display_name, status="active"):
    return {
        "endpoint_id": endpoint_id,
        "metadata": {
            "category": category,
            "display_name": display_name,
            "status": status,
            "updated_at": "2026-08-17T12:00:00Z",
            "date": "2026-08-17T12:00:00Z",
            "tags": ["new"],
        },
    }


def test_collect_models_validates_pages_and_deduplicates():
    from tools.update_fal_catalog import CatalogError, collect_models

    pages = {
        None: {"models": [model(*SAMPLE_MODELS[0])], "has_more": True, "next_cursor": "two"},
        "two": {
            "models": [model(*SAMPLE_MODELS[0]), model(*SAMPLE_MODELS[1])],
            "has_more": False,
            "next_cursor": None,
        },
    }

    result = collect_models(lambda cursor: pages[cursor])
    assert [item["endpoint_id"] for item in result] == [
        "hitem3d/hi3d/texture",
        "meshy/v7/image-to-3d",
    ]

    with pytest.raises(CatalogError, match="models"):
        collect_models(lambda _cursor: {"models": "not-a-list", "has_more": False})


def test_request_headers_use_environment_key_without_persisting_it():
    from tools.update_fal_catalog import request_headers

    assert request_headers({}) == {"Accept": "application/json"}
    headers = request_headers({"FAL_KEY": "secret-value"})
    assert headers == {"Accept": "application/json", "Authorization": "Key secret-value"}


def test_refresh_report_is_compact_unless_verbose(capsys):
    from tools.update_fal_catalog import build_catalog, print_report

    new = build_catalog([model(*SAMPLE_MODELS[0])], generated_at="2026-08-17T12:00:00Z")
    print_report(None, new, verbose=False)
    compact = capsys.readouterr().out
    assert "meshy/v7/image-to-3d" not in compact
    assert "image-to-3d" in compact

    print_report(None, new, verbose=True)
    verbose = capsys.readouterr().out
    assert "meshy/v7/image-to-3d" in verbose


def test_build_catalog_preserves_exact_capability_boundaries():
    from tools.update_fal_catalog import build_catalog, node_type_for_endpoint

    catalog = build_catalog([model(*item) for item in SAMPLE_MODELS], generated_at="2026-08-17T12:00:00Z")

    assert catalog["schema_version"] == 1
    assert set(catalog["categories"]) >= {
        "text-to-image",
        "image-to-image",
        "text-to-video",
        "image-to-video",
        "video-to-video",
        "image-to-3d",
        "3d-to-3d",
    }
    assert "meshy/v7/image-to-3d" in catalog["categories"]["image-to-3d"]
    assert "meshy/v7/image-to-3d" not in catalog["categories"]["text-to-image"]
    assert "blackforestlabs/flux-3/extend-video" in catalog["categories"]["video-to-video"]
    assert "fal-ai/topaz/upscale/image" in catalog["roles"]["image-upscale"]
    assert node_type_for_endpoint(catalog, "meshy/v7/image-to-3d") == "FalImageTo3DAPI"
    assert node_type_for_endpoint(catalog, "blackforestlabs/flux-3/extend-video") == "FalVideoToVideoAPI"
    assert node_type_for_endpoint(catalog, "fal-ai/topaz/upscale/image") == "FalImageUpscaleAPI"


def test_catalog_choice_loader_returns_only_requested_category(tmp_path):
    from comfyui_nodes.capability_catalog import load_endpoint_choices
    from tools.update_fal_catalog import build_catalog

    path = tmp_path / "fal_endpoint_catalog.json"
    path.write_text(
        json.dumps(build_catalog([model(*item) for item in SAMPLE_MODELS], generated_at="2026-08-17T12:00:00Z")),
        encoding="utf-8",
    )

    image_choices = load_endpoint_choices(path, categories=("text-to-image",))
    model_choices = load_endpoint_choices(path, categories=("image-to-3d", "text-to-3d"))

    assert image_choices == ["fal-ai/flux-2"]
    assert model_choices == ["meshy/v7/image-to-3d"]


def test_workflows_use_typed_nodes_matching_endpoint_categories():
    from tools.update_fal_catalog import NODE_TYPE_CATEGORIES

    catalog = json.loads((ROOT / "catalog" / "fal_endpoint_catalog.json").read_text(encoding="utf-8"))
    endpoint_categories = {
        endpoint: category
        for category, endpoints in catalog["categories"].items()
        for endpoint in endpoints
    }

    for path in sorted((ROOT / "workflows_api").glob("*.json")):
        workflow = json.loads(path.read_text(encoding="utf-8"))
        for node in workflow.values():
            node_type = node.get("class_type")
            endpoint = node.get("inputs", {}).get("endpoint")
            if not endpoint or node_type not in NODE_TYPE_CATEGORIES:
                continue
            allowed = NODE_TYPE_CATEGORIES[node_type]
            assert endpoint_categories[endpoint] in allowed, (
                f"{path.name}: {endpoint} is {endpoint_categories[endpoint]}, not valid for {node_type}"
            )


def test_registry_endpoint_lists_match_their_typed_workflow():
    from tools.update_fal_catalog import NODE_TYPE_CATEGORIES

    catalog = json.loads((ROOT / "catalog" / "fal_endpoint_catalog.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "fal_models.json").read_text(encoding="utf-8"))["workflows"]
    for name, metadata in registry.items():
        api_path = ROOT / "workflows_api" / metadata["file"]
        if not api_path.exists():
            continue
        graph = json.loads(api_path.read_text(encoding="utf-8"))
        typed_nodes = {
            node.get("class_type")
            for node in graph.values()
            if node.get("class_type") in NODE_TYPE_CATEGORIES
        }
        if not typed_nodes:
            continue
        assert "FalGenericAPI" not in metadata.get("engine_node", ""), name
        allowed_categories = {
            category for node_type in typed_nodes for category in NODE_TYPE_CATEGORIES[node_type]
        }
        for endpoint in metadata.get("swappable_values", []):
            assert catalog["models"][endpoint]["category"] in allowed_categories, f"{name}: {endpoint}"


def test_no_workflow_uses_legacy_flat_generic_node():
    for directory in (ROOT / "workflows_api", ROOT / "workflows_gui"):
        for path in directory.glob("*.json"):
            assert '"FalGenericAPI"' not in path.read_text(encoding="utf-8"), path.name


def test_workflow_builders_do_not_emit_legacy_flat_generic_node():
    for name in ("build_content_engine.py", "build_video_studio.py", "build_3d_studio.py"):
        source = (ROOT / "tools" / name).read_text(encoding="utf-8")
        assert '"FalGenericAPI"' not in source, name


def test_runner_enforces_typed_endpoint_boundaries():
    import run_fal_workflow as runner

    catalog = json.loads((ROOT / "catalog" / "fal_endpoint_catalog.json").read_text(encoding="utf-8"))
    assert runner.is_fal_endpoint_node("FalTextToImageAPI")
    assert runner.is_fal_endpoint_node("FalImageTo3DAPI")
    assert runner.endpoint_allowed_for_node("FalImageTo3DAPI", "meshy/v7/image-to-3d", catalog)
    assert not runner.endpoint_allowed_for_node("FalTextToImageAPI", "meshy/v7/image-to-3d", catalog)
    assert runner.endpoint_allowed_for_node("FalGenericAPI", "meshy/v7/image-to-3d", catalog)


def test_deploy_workflows_copies_every_gui_graph(tmp_path):
    from tools.update_fal_catalog import deploy_workflows

    destination = tmp_path / "workflows"
    copied = deploy_workflows(destination)
    source_names = {path.name for path in (ROOT / "workflows_gui").glob("*.json")}
    assert copied == len(source_names)
    assert {path.name for path in destination.glob("*.json")} == source_names
    for name in source_names:
        assert (destination / name).read_bytes() == (ROOT / "workflows_gui" / name).read_bytes()
