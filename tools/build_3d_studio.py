"""Build the canonical model-swappable Fal image-to-3D workflow."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "3d_generic_fal"
LEGACY = ("3d_image_to_glb_trellis", "3d_image_to_glb_meshy", "3d_image_to_glb_rodin")
MODELS = [
    "fal-ai/trellis-2",
    "fal-ai/meshy/v6/image-to-3d",
    "fal-ai/meshy/v6/multi-image-to-3d",
    "fal-ai/hyper3d/rodin/v2.5",
    "fal-ai/pixal3d",
    "fal-ai/hunyuan_world/image-to-world",
]


def build_api():
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": "PARAM_IMAGE"}, "_meta": {"title": "Primary image"}},
        "2": {"class_type": "LoadImage", "inputs": {"image": "PARAM_IMAGE_2"}, "_meta": {"title": "Optional second view"}},
        "3": {"class_type": "FalGenericAPI", "inputs": {
            "endpoint": "fal-ai/trellis-2", "prompt": "PARAM_PROMPT",
            "image_1": ["1", 0], "image_2": ["2", 0], "seed": -1,
            "aspect_ratio": "auto", "extra_arguments": "{}"
        }, "_meta": {"title": "Image to 3D - swappable Fal model"}},
        "4": {"class_type": "SaveStringKJ", "inputs": {
            "string": ["3", 1], "filename_prefix": "image_to_3d",
            "output_folder": "output", "file_extension": ".txt"
        }, "_meta": {"title": "Save GLB / asset URL"}},
    }


def load_node(node_id, y, order, link, title):
    return {
        "id": node_id, "type": "LoadImage", "pos": [80, y], "size": [315, 314],
        "flags": {}, "order": order, "mode": 0, "inputs": [],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [link]},
                    {"name": "MASK", "type": "MASK", "links": None}],
        "properties": {"Node name for S&R": "LoadImage"}, "title": title,
        "widgets_values": ["example.png", "image"],
    }


def build_gui():
    nodes = [
        load_node(1, 180, 0, 1, "PRIMARY VIEW - uploads to Fal"),
        load_node(2, 590, 1, 2, "SECOND VIEW - Meshy Multi / Rodin"),
        {
            "id": 3, "type": "FalGenericAPI", "pos": [500, 260], "size": [520, 390],
            "flags": {}, "order": 2, "mode": 0,
            "inputs": [{"name": "image_1", "type": "IMAGE", "link": 1, "shape": 7},
                       {"name": "image_2", "type": "IMAGE", "link": 2, "shape": 7}],
            "outputs": [{"name": "image", "type": "IMAGE", "links": None},
                        {"name": "raw_response_or_url", "type": "STRING", "links": [3]}],
            "properties": {"Node name for S&R": "FalGenericAPI"},
            "title": "IMAGE TO 3D - SELECT MODEL",
            "widgets_values": ["fal-ai/trellis-2", "", -1, "fixed", "auto", "{}"],
        },
        {
            "id": 4, "type": "SaveStringKJ", "pos": [1100, 330], "size": [420, 220],
            "flags": {}, "order": 3, "mode": 0,
            "inputs": [{"name": "string", "type": "STRING", "link": 3, "widget": {"name": "string"}}],
            "outputs": [{"name": "filename", "type": "STRING", "links": None}],
            "properties": {"Node name for S&R": "SaveStringKJ"},
            "title": "SAVE GLB / ASSET URL", "widgets_values": ["", "image_to_3d", "output", ".txt"],
        },
    ]
    return {
        "id": "image-to-3d-studio-ui", "revision": 0, "last_node_id": 4, "last_link_id": 3,
        "nodes": nodes,
        "links": [[1, 1, 0, 3, 0, "IMAGE"], [2, 2, 0, 3, 1, "IMAGE"], [3, 3, 1, 4, 0, "STRING"]],
        "groups": [
            {"id": 1, "title": "SOURCE VIEWS", "bounding": [40, 100, 400, 850], "color": "#3f789e", "font_size": 24, "flags": {}},
            {"id": 2, "title": "MODEL + OUTPUT", "bounding": [460, 180, 1110, 550], "color": "#4f7f63", "font_size": 24, "flags": {}},
        ],
        "config": {},
        "extra": {"image_to_3d": {"models": MODELS,
            "multi_view_models": ["fal-ai/meshy/v6/multi-image-to-3d", "fal-ai/hyper3d/rodin/v2.5"],
            "security_notice": "Input images are uploaded to Fal. Do not use confidential project imagery unless transfer is permitted."
        }, "ds": {"scale": 0.85, "offset": [20, 20]}},
        "version": 0.4,
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    write_json(ROOT / "workflows_api" / f"{NAME}.json", build_api())
    write_json(ROOT / "workflows_gui" / f"{NAME}.json", build_gui())
    path = ROOT / "fal_models.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    for name in LEGACY:
        registry["workflows"].pop(name, None)
    registry["workflows"][NAME] = {
        "file": f"{NAME}.json", "purpose": "Canonical single- or multi-view image-to-3D workflow with swappable Fal models.",
        "auth": "fal", "needs_image": True, "engine_node": "FalGenericAPI",
        "swappable_field": "endpoint", "swappable_values": MODELS,
        "note": "Trellis, Meshy single, Pixal3D, and Hunyuan use the primary view. Meshy Multi and Rodin use both views. Hunyuan returns a world asset rather than a conventional object mesh."
    }
    write_json(path, registry)


if __name__ == "__main__":
    main()
