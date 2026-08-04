import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI_PATH = ROOT / "workflows_gui" / "video_studio_fal.json"
API_PATH = ROOT / "workflows_api" / "video_studio_fal.json"
REGISTRY_PATH = ROOT / "fal_models.json"
MAPPER_PATH = (
    ROOT.parent / "Comfy" / "ComfyUI" / "custom_nodes" / "fal-api" / "nodes"
    / "endpoint_image_arguments.py"
)


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
            if node.get("class_type") == "FalGenericAPI"
        }
        self.assertEqual(
            endpoints,
            {
                "bytedance/seedance-2.0/text-to-video",
                "bytedance/seedance-2.0/image-to-video",
                "bytedance/seedance-2.0/reference-to-video",
            },
        )
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


if __name__ == "__main__":
    unittest.main()
