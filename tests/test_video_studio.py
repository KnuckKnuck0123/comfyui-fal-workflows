import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI_PATH = ROOT / "workflows_gui" / "video_studio_fal.json"
API_PATH = ROOT / "workflows_api" / "video_studio_fal.json"
REGISTRY_PATH = ROOT / "fal_models.json"
MAPPER_PATH = ROOT / "comfyui_nodes" / "endpoint_image_arguments.py"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class VideoStudioContractTests(unittest.TestCase):
    def test_video_studio_exists_in_gui_api_and_registry(self):
        self.assertTrue(GUI_PATH.is_file())
        self.assertTrue(API_PATH.is_file())
        registry = load_json(REGISTRY_PATH)["workflows"]["video_studio_fal"]
        self.assertEqual(registry["default_mode"], "text_to_video")
        self.assertEqual(
            registry["mode_precedence"],
            ["reference_to_video", "first_last_frame", "image_to_video", "text_to_video"],
        )

    def test_api_uses_four_seedance_modes_and_lazy_url_routing(self):
        graph = load_json(API_PATH)
        endpoints = {
            node["inputs"]["endpoint"]
            for node in graph.values()
            if node.get("class_type") in {"FalTextToVideoAPI", "FalImageToVideoAPI"}
        }
        self.assertEqual(
            endpoints,
            {
                "bytedance/seedance-2.0/text-to-video",
                "bytedance/seedance-2.0/image-to-video",
                "bytedance/seedance-2.0/reference-to-video",
            },
        )
        self.assertEqual(graph["1"]["class_type"], "FalTextToVideoAPI")
        self.assertTrue(all(graph[node_id]["class_type"] == "FalImageToVideoAPI" for node_id in ("3", "5", "7")))
        switches = [n for n in graph.values() if n.get("class_type") == "LazySwitchKJ"]
        self.assertEqual(len(switches), 3)
        for switch in switches:
            self.assertEqual(switch["inputs"]["switch"], False)
        save = next(n for n in graph.values() if n.get("class_type") == "SaveStringKJ")
        self.assertEqual(save["inputs"]["string"], ["10", 0])

    def test_endpoint_upload_mapper_uses_fal_schema_fields(self):
        spec = importlib.util.spec_from_file_location("endpoint_image_arguments", MAPPER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(
            module.map_uploaded_images(
                "bytedance/seedance-2.0/image-to-video", ["start", "end"]
            ),
            {"image_url": "start", "end_image_url": "end"},
        )
        self.assertEqual(
            module.map_uploaded_images(
                "bytedance/seedance-2.0/reference-to-video", ["one", "two"]
            ),
            {"image_urls": ["one", "two"]},
        )
        first_last_endpoints = (
            "blackforestlabs/flux-3/first-last-frame-to-video",
            "lightricks/ltx-2.5/image-to-video/pro",
            "minimax/h3/image-to-video",
            "bytedance/seedance-2.5/image-to-video",
        )
        for endpoint in first_last_endpoints:
            expected = {"image_url": "start", "end_image_url": "end"}
            if "flux-3/first-last" in endpoint:
                expected = {"start_image_url": "start", "end_image_url": "end"}
            self.assertEqual(module.map_uploaded_images(endpoint, ["start", "end"]), expected)
        self.assertEqual(
            module.map_uploaded_images("blackforestlabs/flux-3/image-to-video", ["start", "unused"]),
            {"image_url": "start"},
        )
        self.assertEqual(
            module.map_uploaded_images("minimax/h3/reference-to-video", ["one", "two"]),
            {"reference_image_urls": ["one", "two"]},
        )
        self.assertEqual(
            module.map_uploaded_images("bytedance/seedance-2.5/reference-to-video", ["one", "two"]),
            {"image_urls": ["one", "two"]},
        )


if __name__ == "__main__":
    unittest.main()
