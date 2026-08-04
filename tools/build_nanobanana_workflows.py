"""Generate the canonical Nano Banana GUI/API workflow pairs."""

import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = ROOT / "workflows_gui"
API_DIR = ROOT / "workflows_api"

SPECS = {
    "nanobanana_edit_inpaint": ("Nano Banana 2", "inpaint", "2K"),
    "nanobanana_2_generate": ("Nano Banana 2", "generate", "2K"),
    "nanobanana_pro_generate": ("Nano Banana Pro", "generate", "4K"),
}

INPAINT_SYSTEM_PROMPT = (
    "Perform semantic inpainting. Change only the element or region named in the user prompt. "
    "Keep everything else exactly the same, preserving composition, geometry, perspective, "
    "materials, lighting, color, and style."
)


def nano_inputs(model, prompt, image_size, image_ref=None, system_prompt=""):
    inputs = {
        "prompt": prompt,
        "model": model,
        "batch_size": 1,
        "seed": 42,
        "system_prompt": system_prompt,
        "api_key": "",
        "aspect_ratio": "auto",
        "image_size": image_size,
    }
    if image_ref is not None:
        inputs["images"] = image_ref
    return inputs


def api_graph(name, model, mode, image_size):
    edit = mode != "generate"
    action = "Inpaint" if mode == "inpaint" else ("Edit" if edit else "Generate")
    nano_id = "2" if edit else "1"
    graph = {}
    if edit:
        graph["1"] = {
            "class_type": "LoadImage",
            "inputs": {"image": "PARAM_IMAGE"},
            "_meta": {"title": "Load image to edit"},
        }
    graph[nano_id] = {
        "class_type": "NanoBananaGeminiImageNode",
        "inputs": nano_inputs(
            model,
            "PARAM_PROMPT",
            image_size,
            ["1", 0] if edit else None,
            INPAINT_SYSTEM_PROMPT if mode == "inpaint" else "",
        ),
        "_meta": {"title": f"{model} - {action}"},
    }
    graph[str(int(nano_id) + 1)] = {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": name, "images": [nano_id, 0]},
        "_meta": {"title": "Save image"},
    }
    return graph


def gui_node(node_id, node_type, pos, size, order, inputs, outputs, widgets, title):
    return {
        "id": node_id,
        "type": node_type,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": node_type, "title": title},
        "widgets_values": widgets,
    }


def gui_graph(name, model, mode, image_size):
    edit = mode != "generate"
    action = "Inpaint" if mode == "inpaint" else ("Edit" if edit else "Generate")
    nodes = []
    links = []
    nano_id = 2 if edit else 1
    nano_order = 1 if edit else 0
    if edit:
        nodes.append(gui_node(
            1, "LoadImage", [80, 240], [315, 314], 0, [],
            [{"name": "IMAGE", "type": "IMAGE", "links": [1]},
             {"name": "MASK", "type": "MASK", "links": None}],
            ["example.png", "image"], "Load image to edit",
        ))
        links.append([1, 1, 0, 2, 0, "IMAGE"])
    nano_inputs_gui = []
    if edit:
        nano_inputs_gui.append({"name": "images", "type": "IMAGE", "link": 1})
    nodes.append(gui_node(
        nano_id, "NanoBananaGeminiImageNode", [460 if edit else 100, 220], [420, 430], nano_order,
        nano_inputs_gui,
        [{"name": "images", "type": "IMAGE", "links": [2, 3]},
         {"name": "text", "type": "STRING", "links": None}],
        [
            "Change only [specific element or region] to [replacement]. Keep everything else exactly the same." if mode == "inpaint"
            else "Edit this image while preserving its composition and architectural intent." if edit
            else "Create a high-quality architectural concept image.",
            model, 1, 42, INPAINT_SYSTEM_PROMPT if mode == "inpaint" else "", "", "auto", image_size,
        ],
        f"{model} - {action}",
    ))
    save_id = nano_id + 1
    preview_id = nano_id + 2
    nodes.append(gui_node(
        save_id, "SaveImage", [940 if edit else 580, 180], [400, 450], nano_order + 1,
        [{"name": "images", "type": "IMAGE", "link": 2}], [], [name], "Save image",
    ))
    nodes.append(gui_node(
        preview_id, "PreviewImage", [940 if edit else 580, 690], [400, 400], nano_order + 2,
        [{"name": "images", "type": "IMAGE", "link": 3}], [], [], "Preview image",
    ))
    links.extend([[2, nano_id, 0, save_id, 0, "IMAGE"], [3, nano_id, 0, preview_id, 0, "IMAGE"]])
    return {
        "id": name.replace("_", "-") + "-ui",
        "revision": 0,
        "last_node_id": preview_id,
        "last_link_id": 3,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"ds": {"scale": 1, "offset": [0, 0]}},
        "version": 0.4,
    }


def migrate_api(path):
    graph = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for node in graph.values():
        if node.get("class_type") != "NanoBanana API\U0001f34c":
            continue
        changed = True
        old = node["inputs"]
        image_ref = old.get("image")
        raw_model = old.get("model_name", "")
        model = "Nano Banana Pro" if "pro" in raw_model.lower() else "Nano Banana 2"
        node["class_type"] = "NanoBananaGeminiImageNode"
        node["inputs"] = nano_inputs(model, old.get("prompt", "PARAM_PROMPT"), "auto", image_ref)
        node["_meta"] = {"title": f"{model} - Edit"}
    if changed:
        path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_gui(path):
    graph = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for node in graph["nodes"]:
        if node.get("type") != "NanoBanana API\U0001f34c":
            continue
        changed = True
        widgets = node.get("widgets_values", [])
        raw_model = widgets[1] if len(widgets) > 1 else ""
        model = "Nano Banana Pro" if "pro" in str(raw_model).lower() else "Nano Banana 2"
        prompt = widgets[0] if widgets else "Edit this image."
        for item in node.get("inputs", []):
            if item.get("name") == "image":
                item["name"] = "images"
        node["type"] = "NanoBananaGeminiImageNode"
        node["properties"] = {"Node name for S&R": "NanoBananaGeminiImageNode", "title": f"{model} - Edit"}
        node["outputs"] = [
            {"name": "images", "type": "IMAGE", "links": node.get("outputs", [{}])[0].get("links")},
            {"name": "text", "type": "STRING", "links": None},
        ]
        node["widgets_values"] = [prompt, model, 1, 42, "", "", "auto", "auto"]
    if changed:
        path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    for name, (model, mode, image_size) in SPECS.items():
        (API_DIR / f"{name}.json").write_text(
            json.dumps(api_graph(name, model, mode, image_size), indent=2) + "\n", encoding="utf-8"
        )
        (GUI_DIR / f"{name}.json").write_text(
            json.dumps(gui_graph(name, model, mode, image_size), indent=2) + "\n", encoding="utf-8"
        )
    registry_path = ROOT / "fal_models.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    workflows = registry["workflows"]
    for name, (model, mode, image_size) in SPECS.items():
        edit = mode != "generate"
        action = "Semantically inpaint an input image" if mode == "inpaint" else (
            "Edit an input image" if edit else "Generate an image from text"
        )
        workflows[name] = {
            "file": f"{name}.json",
            "purpose": f"{action} with {model} through the dedicated Google Gemini node.",
            "auth": "gemini",
            "needs_image": edit,
            "engine_node": "NanoBananaGeminiImageNode",
            "model": model,
            "image_size": image_size,
        }
        if mode == "inpaint":
            workflows[name]["edit_mode"] = "semantic_masking"
            workflows[name]["note"] = (
                "The official Gemini node has no mask socket. Name the target region precisely in the prompt; "
                "Nano Banana performs conversational semantic masking."
            )
        if name == "nanobanana_edit_inpaint":
            workflows[name]["purpose"] = (
                "Unified image editing and semantic inpainting with a swappable Nano Banana model."
            )
            workflows[name]["swappable_field"] = "model"
            workflows[name]["swappable_values"] = ["Nano Banana 2", "Nano Banana Pro"]
    for name in (
        "render_nanobanana_gemini",
        "refine_nanobanana_chain",
        "refine_from_output",
        "refine_multi_engine_chain",
    ):
        meta = workflows[name]
        meta["engine_node"] = meta["engine_node"].replace(
            "NanoBanana API\U0001f34c", "NanoBananaGeminiImageNode"
        )
        if name == "render_nanobanana_gemini":
            meta["swappable_field"] = "model"
            meta["swappable_values"] = ["Nano Banana 2", "Nano Banana Pro"]
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for folder, migrate in ((API_DIR, migrate_api), (GUI_DIR, migrate_gui)):
        for path in folder.glob("*.json"):
            migrate(path)


if __name__ == "__main__":
    main()
