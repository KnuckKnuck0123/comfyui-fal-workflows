"""Build the hosted Fal Video Studio GUI/API workflow pair."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "video_studio_fal"
DEFAULTS = '{"resolution":"720p","duration":"5","generate_audio":true}'


def fal_inputs(endpoint, prompt, image_1=None, image_2=None):
    inputs = {
        "endpoint": endpoint,
        "prompt": prompt,
        "seed": -1,
        "aspect_ratio": "16:9",
        "extra_arguments": DEFAULTS,
    }
    if image_1 is not None:
        inputs["image_1"] = image_1
    if image_2 is not None:
        inputs["image_2"] = image_2
    return inputs


def build_api():
    return {
        "1": {"class_type": "FalGenericAPI", "inputs": fal_inputs(
            "bytedance/seedance-2.0/text-to-video", "PARAM_PROMPT"
        ), "_meta": {"title": "1 - Text to video"}},
        "2": {"class_type": "LoadImage", "inputs": {"image": "PARAM_IMAGE"},
              "_meta": {"title": "Start / primary reference image"}},
        "3": {"class_type": "FalGenericAPI", "inputs": fal_inputs(
            "bytedance/seedance-2.0/image-to-video", "PARAM_PROMPT", ["2", 0]
        ), "_meta": {"title": "2 - Image to video"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": "PARAM_IMAGE_2"},
              "_meta": {"title": "End frame"}},
        "5": {"class_type": "FalGenericAPI", "inputs": fal_inputs(
            "bytedance/seedance-2.0/image-to-video", "PARAM_PROMPT", ["2", 0], ["4", 0]
        ), "_meta": {"title": "3 - First / last frame"}},
        "6": {"class_type": "LoadImage", "inputs": {"image": "PARAM_IMAGE_2"},
              "_meta": {"title": "Second reference image"}},
        "7": {"class_type": "FalGenericAPI", "inputs": fal_inputs(
            "bytedance/seedance-2.0/reference-to-video", "PARAM_PROMPT", ["2", 0], ["6", 0]
        ), "_meta": {"title": "4 - Reference to video; prompt with @Image1 and @Image2"}},
        "8": {"class_type": "LazySwitchKJ", "inputs": {
            "switch": False, "on_false": ["1", 1], "on_true": ["3", 1]
        }, "_meta": {"title": "Image-to-video mode"}},
        "9": {"class_type": "LazySwitchKJ", "inputs": {
            "switch": False, "on_false": ["8", 0], "on_true": ["5", 1]
        }, "_meta": {"title": "First / last-frame mode"}},
        "10": {"class_type": "LazySwitchKJ", "inputs": {
            "switch": False, "on_false": ["9", 0], "on_true": ["7", 1]
        }, "_meta": {"title": "Reference-to-video mode"}},
        "11": {"class_type": "SaveStringKJ", "inputs": {
            "string": ["10", 0], "filename_prefix": "video_studio",
            "output_folder": "output", "file_extension": ".txt"
        }, "_meta": {"title": "Save selected video URL"}},
        "12": {"class_type": "LoadVideoURL", "inputs": {
            "url": ["10", 0], "force_rate": 0, "force_size": "Disabled",
            "custom_width": 512, "custom_height": 512, "frame_load_cap": 30,
            "skip_first_frames": 0, "select_every_nth": 4
        }, "_meta": {"title": "Decode selected video for preview"}},
        "13": {"class_type": "PreviewImage", "inputs": {"images": ["12", 0]},
               "_meta": {"title": "Video preview"}},
    }


def node(node_id, kind, pos, size, order, inputs, outputs, widgets, title):
    return {
        "id": node_id, "type": kind, "pos": pos, "size": size, "flags": {},
        "order": order, "mode": 0, "inputs": inputs, "outputs": outputs,
        "properties": {"Node name for S&R": kind}, "title": title,
        "widgets_values": widgets,
    }


def load_node(node_id, pos, order, links, title):
    return node(node_id, "LoadImage", pos, [315, 314], order, [], [
        {"name": "IMAGE", "type": "IMAGE", "links": links},
        {"name": "MASK", "type": "MASK", "links": None},
    ], ["example.png", "image"], title)


def fal_node(node_id, pos, order, endpoint, prompt, url_link, image_1=None, image_2=None, title=""):
    return node(node_id, "FalGenericAPI", pos, [470, 340], order, [
        {"name": "image_1", "type": "IMAGE", "link": image_1, "shape": 7},
        {"name": "image_2", "type": "IMAGE", "link": image_2, "shape": 7},
    ], [
        {"name": "image", "type": "IMAGE", "links": None},
        {"name": "raw_response_or_url", "type": "STRING", "links": [url_link]},
    ], [endpoint, prompt, -1, "fixed", "16:9", DEFAULTS], title)


def switch_node(node_id, pos, order, false_link, true_link, output_link, title):
    return node(node_id, "LazySwitchKJ", pos, [280, 110], order, [
        {"name": "on_false", "type": "*", "link": false_link},
        {"name": "on_true", "type": "*", "link": true_link},
    ], [{"name": "*", "type": "*", "links": output_link}], [False], title)


def build_gui():
    nodes = [
        fal_node(1, [80, 120], 0, "bytedance/seedance-2.0/text-to-video",
                 "Cinematic architectural sequence, deliberate camera movement, realistic motion",
                 1, title="1 - TEXT TO VIDEO"),
        load_node(2, [80, 600], 1, [2, 4, 7], "START / PRIMARY REFERENCE - uploads to Fal"),
        fal_node(3, [460, 600], 2, "bytedance/seedance-2.0/image-to-video",
                 "Slow cinematic dolly forward, subtle environmental movement", 3, 2,
                 title="2 - IMAGE TO VIDEO"),
        load_node(4, [80, 1080], 3, [5], "END FRAME - uploads to Fal"),
        fal_node(5, [460, 1080], 4, "bytedance/seedance-2.0/image-to-video",
                 "Create a coherent cinematic transition from the start frame to the end frame", 6, 4, 5,
                 "3 - FIRST / LAST FRAME"),
        load_node(6, [80, 1560], 5, [8], "SECOND REFERENCE - uploads to Fal"),
        fal_node(7, [460, 1560], 6, "bytedance/seedance-2.0/reference-to-video",
                 "Use @Image1 as the primary scene and @Image2 as a visual reference. Preserve identity and design.",
                 9, 7, 8, "4 - REFERENCE TO VIDEO"),
        switch_node(8, [1060, 560], 7, 1, 3, [10], "IMAGE-TO-VIDEO MODE"),
        switch_node(9, [1390, 980], 8, 10, 6, [11], "FIRST / LAST-FRAME MODE"),
        switch_node(10, [1720, 1400], 9, 11, 9, [12, 13], "REFERENCE-TO-VIDEO MODE"),
        node(11, "SaveStringKJ", [2080, 1180], [400, 200], 10,
             [{"name": "string", "type": "STRING", "link": 12, "widget": {"name": "string"}}],
             [{"name": "filename", "type": "STRING", "links": None}],
             ["", "video_studio", "output", ".txt"], "SAVE SELECTED VIDEO URL"),
        node(12, "LoadVideoURL", [2080, 1460], [400, 340], 11,
             [{"name": "url", "type": "STRING", "link": 13, "widget": {"name": "url"}}],
             [{"name": "frames", "type": "IMAGE", "links": [14]},
              {"name": "frame_count", "type": "INT", "links": None},
              {"name": "video_info", "type": "VHS_VIDEOINFO", "links": None}],
             ["", 0, "Disabled", 512, 512, 30, 0, 4], "DECODE SELECTED VIDEO FOR PREVIEW"),
        node(13, "PreviewImage", [2540, 1400], [520, 500], 12,
             [{"name": "images", "type": "IMAGE", "link": 14}], [], [], "VIDEO PREVIEW"),
    ]
    links = [
        [1, 1, 1, 8, 0, "*"], [2, 2, 0, 3, 0, "IMAGE"],
        [3, 3, 1, 8, 1, "*"], [4, 2, 0, 5, 0, "IMAGE"],
        [5, 4, 0, 5, 1, "IMAGE"], [6, 5, 1, 9, 1, "*"],
        [7, 2, 0, 7, 0, "IMAGE"], [8, 6, 0, 7, 1, "IMAGE"],
        [9, 7, 1, 10, 1, "*"], [10, 8, 0, 9, 0, "*"],
        [11, 9, 0, 10, 0, "*"], [12, 10, 0, 11, 0, "*"],
        [13, 10, 0, 12, 0, "*"], [14, 12, 0, 13, 0, "IMAGE"],
    ]
    return {
        "id": "video-studio-fal-ui", "revision": 0, "last_node_id": 13,
        "last_link_id": 14, "nodes": nodes, "links": links,
        "groups": [
            {"id": 1, "title": "VIDEO MODES", "bounding": [40, 50, 950, 1930], "color": "#3f789e", "font_size": 24, "flags": {}},
            {"id": 2, "title": "LAZY ROUTING - ONLY SELECTED PAID BRANCH RUNS", "bounding": [1020, 480, 1030, 1100], "color": "#555555", "font_size": 24, "flags": {}},
            {"id": 3, "title": "OUTPUT + PREVIEW", "bounding": [2040, 1100, 1060, 850], "color": "#4f7f63", "font_size": 24, "flags": {}},
        ],
        "config": {},
        "extra": {"video_studio": {
            "default_mode": "text_to_video",
            "mode_precedence": ["reference_to_video", "first_last_frame", "image_to_video", "text_to_video"],
            "security_notice": "Image modes upload source images to Fal. Do not use confidential project imagery unless transfer is permitted."
        }, "ds": {"scale": 0.6, "offset": [20, 20]}},
        "version": 0.4,
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    write_json(ROOT / "workflows_api" / f"{NAME}.json", build_api())
    write_json(ROOT / "workflows_gui" / f"{NAME}.json", build_gui())
    path = ROOT / "fal_models.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["workflows"][NAME] = {
        "file": f"{NAME}.json",
        "purpose": "Fal Video Studio with lazy-routed text, image, first/last-frame, and reference-to-video modes.",
        "auth": "fal", "needs_image": False,
        "engine_node": "FalGenericAPI (x4) + LazySwitchKJ (x3)",
        "default_mode": "text_to_video",
        "mode_precedence": ["reference_to_video", "first_last_frame", "image_to_video", "text_to_video"],
        "note": "Only the selected paid branch executes. Image modes upload source images to Fal."
    }
    write_json(path, registry)


if __name__ == "__main__":
    main()
