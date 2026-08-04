"""Build the hosted-first Content Engine Image Studio workflow pair."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "content_engine_image_studio"


def fal_inputs(endpoint, prompt, extra_arguments="{}", image=None):
    inputs = {
        "endpoint": endpoint,
        "prompt": prompt,
        "seed": -1,
        "aspect_ratio": "16:9",
        "extra_arguments": extra_arguments,
    }
    if image is not None:
        inputs["image_1"] = image
    return inputs


def build_api():
    return {
        "1": {
            "class_type": "FalGenericAPI",
            "inputs": fal_inputs(
                "fal-ai/flux-2",
                "PARAM_PROMPT",
                '{"image_size":"landscape_16_9","num_images":1}',
            ),
            "_meta": {"title": "1 - Generate"},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": "PARAM_IMAGE"},
            "_meta": {"title": "Edit source - uploaded to Fal when selected"},
        },
        "3": {
            "class_type": "FalGenericAPI",
            "inputs": fal_inputs(
                "openai/gpt-image-2/edit", "PARAM_PROMPT", "{}", ["2", 0]
            ),
            "_meta": {"title": "2 - Edit / Render"},
        },
        "4": {
            "class_type": "FalGenericAPI",
            "inputs": fal_inputs(
                "fal-ai/flux-2",
                "PARAM_PROMPT",
                '{"image_size":"landscape_16_9","num_images":4}',
            ),
            "_meta": {"title": "3 - Variations"},
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "PARAM_IMAGE"},
            "_meta": {"title": "Upscale source - uploaded to Fal when selected"},
        },
        "6": {
            "class_type": "FalGenericAPI",
            "inputs": fal_inputs(
                "fal-ai/topaz/upscale/image", "", "{}", ["5", 0]
            ),
            "_meta": {"title": "4 - Upscale"},
        },
        "7": {
            "class_type": "LazySwitchKJ",
            "inputs": {"switch": False, "on_false": ["1", 0], "on_true": ["3", 0]},
            "_meta": {"title": "Edit mode"},
        },
        "8": {
            "class_type": "LazySwitchKJ",
            "inputs": {"switch": False, "on_false": ["7", 0], "on_true": ["4", 0]},
            "_meta": {"title": "Variations mode"},
        },
        "9": {
            "class_type": "LazySwitchKJ",
            "inputs": {"switch": False, "on_false": ["8", 0], "on_true": ["6", 0]},
            "_meta": {"title": "Upscale mode"},
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "content_engine", "images": ["9", 0]},
            "_meta": {"title": "Save selected result"},
        },
        "11": {
            "class_type": "PreviewImage",
            "inputs": {"images": ["9", 0]},
            "_meta": {"title": "Preview selected result"},
        },
    }


def node(node_id, kind, pos, size, order, inputs, outputs, widgets, title):
    return {
        "id": node_id,
        "type": kind,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": kind},
        "title": title,
        "widgets_values": widgets,
    }


def fal_node(node_id, pos, order, endpoint, prompt, extra, output_link, title, image_link=None):
    inputs = [
        {"name": "image_1", "type": "IMAGE", "link": image_link, "shape": 7},
        {"name": "image_2", "type": "IMAGE", "link": None, "shape": 7},
    ]
    return node(
        node_id,
        "FalGenericAPI",
        pos,
        [470, 340],
        order,
        inputs,
        [
            {"name": "image", "type": "IMAGE", "links": [output_link]},
            {"name": "raw_response_or_url", "type": "STRING", "links": None},
        ],
        [endpoint, prompt, -1, "fixed", "16:9", extra],
        title,
    )


def load_node(node_id, pos, order, output_link, title):
    return node(
        node_id,
        "LoadImage",
        pos,
        [315, 314],
        order,
        [],
        [
            {"name": "IMAGE", "type": "IMAGE", "links": [output_link]},
            {"name": "MASK", "type": "MASK", "links": None},
        ],
        ["example.png", "image"],
        title,
    )


def switch_node(node_id, pos, order, false_link, true_link, output_link, title):
    return node(
        node_id,
        "LazySwitchKJ",
        pos,
        [260, 110],
        order,
        [
            {"name": "on_false", "type": "*", "link": false_link},
            {"name": "on_true", "type": "*", "link": true_link},
        ],
        [{"name": "*", "type": "*", "links": output_link}],
        [False],
        title,
    )


def build_gui():
    nodes = [
        fal_node(
            1, [80, 130], 0, "fal-ai/flux-2",
            "architectural concept image, editorial composition, compelling light",
            '{"image_size":"landscape_16_9","num_images":1}', 1, "1 - GENERATE",
        ),
        load_node(2, [80, 650], 1, 2, "Edit source - uploads input images to Fal"),
        fal_node(
            3, [460, 650], 2, "openai/gpt-image-2/edit",
            "transform this source while preserving its composition and architectural intent",
            "{}", 3, "2 - EDIT / RENDER", 2,
        ),
        fal_node(
            4, [80, 1170], 3, "fal-ai/flux-2",
            "architectural concept image, four distinct design directions",
            '{"image_size":"landscape_16_9","num_images":4}', 4, "3 - VARIATIONS",
        ),
        load_node(5, [80, 1690], 4, 6, "Upscale source - uploads input images to Fal"),
        fal_node(
            6, [460, 1690], 5, "fal-ai/topaz/upscale/image", "", "{}", 7,
            "4 - UPSCALE", 6,
        ),
        switch_node(7, [1040, 570], 6, 1, 3, [5], "EDIT MODE"),
        switch_node(8, [1360, 960], 7, 5, 4, [8], "VARIATIONS MODE"),
        switch_node(9, [1680, 1350], 8, 8, 7, [9, 10], "UPSCALE MODE"),
        node(
            10, "SaveImage", [2040, 1150], [400, 450], 9,
            [{"name": "images", "type": "IMAGE", "link": 9}], [],
            ["content_engine"], "SAVE SELECTED RESULT",
        ),
        node(
            11, "PreviewImage", [2040, 1640], [400, 400], 10,
            [{"name": "images", "type": "IMAGE", "link": 10}], [], [],
            "PREVIEW SELECTED RESULT",
        ),
    ]
    links = [
        [1, 1, 0, 7, 0, "*"],
        [2, 2, 0, 3, 0, "IMAGE"],
        [3, 3, 0, 7, 1, "*"],
        [4, 4, 0, 8, 1, "*"],
        [5, 7, 0, 8, 0, "*"],
        [6, 5, 0, 6, 0, "IMAGE"],
        [7, 6, 0, 9, 1, "*"],
        [8, 8, 0, 9, 0, "*"],
        [9, 9, 0, 10, 0, "*"],
        [10, 9, 0, 11, 0, "*"],
    ]
    return {
        "id": "content-engine-image-studio-ui",
        "revision": 0,
        "last_node_id": 11,
        "last_link_id": 10,
        "nodes": nodes,
        "links": links,
        "groups": [
            {"id": 1, "title": "1 - GENERATE", "bounding": [40, 60, 560, 450], "color": "#3f789e", "font_size": 24, "flags": {}},
            {"id": 2, "title": "2 - EDIT / RENDER", "bounding": [40, 570, 940, 430], "color": "#8a5f3d", "font_size": 24, "flags": {}},
            {"id": 3, "title": "3 - VARIATIONS", "bounding": [40, 1100, 560, 450], "color": "#6f5587", "font_size": 24, "flags": {}},
            {"id": 4, "title": "4 - UPSCALE", "bounding": [40, 1610, 940, 430], "color": "#4f7f63", "font_size": 24, "flags": {}},
            {"id": 5, "title": "ROUTING + OUTPUT", "bounding": [1000, 490, 1500, 1580], "color": "#555555", "font_size": 24, "flags": {}},
        ],
        "config": {},
        "extra": {
            "content_engine": {
                "mode_precedence": ["upscale", "variations", "edit", "generate"],
                "default_mode": "generate",
                "security_notice": "Edit and upscale modes upload input images to Fal. Do not use confidential project imagery unless transfer is permitted.",
            },
            "ds": {"scale": 0.65, "offset": [40, 20]},
        },
        "version": 0.4,
    }


def write_json(path, value):
    rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != rendered:
        path.write_text(rendered, encoding="utf-8")


def main():
    write_json(ROOT / "workflows_api" / f"{NAME}.json", build_api())
    write_json(ROOT / "workflows_gui" / f"{NAME}.json", build_gui())

    path = ROOT / "fal_models.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["workflows"][NAME] = {
        "file": f"{NAME}.json",
        "purpose": "Hosted-first Image Studio with safely routed Generate, Edit / Render, Variations, and Upscale modes.",
        "auth": "fal",
        "needs_image": False,
        "engine_node": "FalGenericAPI (x4) + LazySwitchKJ (x3)",
        "default_mode": "generate",
        "mode_precedence": ["upscale", "variations", "edit", "generate"],
        "note": "Only the selected lazy branch executes. Edit and upscale upload input images to Fal.",
    }
    write_json(path, registry)


if __name__ == "__main__":
    main()
