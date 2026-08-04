import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI_PATH = ROOT / "workflows_gui" / "content_engine_image_studio.json"
API_PATH = ROOT / "workflows_api" / "content_engine_image_studio.json"
REGISTRY_PATH = ROOT / "fal_models.json"

EXPECTED_ENDPOINTS = {
    "fal-ai/flux-2",
    "openai/gpt-image-2/edit",
    "fal-ai/topaz/upscale/image",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ContentEngineImageStudioTests(unittest.TestCase):
    def test_gui_and_api_workflows_exist(self):
        self.assertTrue(GUI_PATH.is_file())
        self.assertTrue(API_PATH.is_file())

    def test_api_has_four_fal_branches_and_three_lazy_switches(self):
        graph = load(API_PATH)
        nodes = list(graph.values())
        fal_nodes = [node for node in nodes if node.get("class_type") == "FalGenericAPI"]
        switches = [node for node in nodes if node.get("class_type") == "LazySwitchKJ"]
        self.assertEqual(len(fal_nodes), 4)
        self.assertEqual(len(switches), 3)
        self.assertEqual({node["inputs"]["endpoint"] for node in fal_nodes}, EXPECTED_ENDPOINTS)
        self.assertTrue(all(node["inputs"]["switch"] is False for node in switches))

    def test_only_one_shared_save_and_preview_output_exists(self):
        for path, api_format in ((API_PATH, True), (GUI_PATH, False)):
            with self.subTest(path=path.name):
                graph = load(path)
                nodes = list(graph.values()) if api_format else graph["nodes"]
                field = "class_type" if api_format else "type"
                self.assertEqual(sum(node.get(field) == "SaveImage" for node in nodes), 1)
                self.assertEqual(sum(node.get(field) == "PreviewImage" for node in nodes), 1)

    def test_gui_documents_modes_and_upload_boundary(self):
        graph = load(GUI_PATH)
        titles = {group["title"] for group in graph["groups"]}
        self.assertTrue({"1 - GENERATE", "2 - EDIT / RENDER", "3 - VARIATIONS", "4 - UPSCALE", "ROUTING + OUTPUT"}.issubset(titles))
        serialized = json.dumps(graph).lower()
        self.assertIn("uploads input images to fal", serialized)

    def test_registry_marks_engine_as_fal_and_default_generate(self):
        meta = load(REGISTRY_PATH)["workflows"]["content_engine_image_studio"]
        self.assertEqual(meta["auth"], "fal")
        self.assertFalse(meta["needs_image"])
        self.assertEqual(meta["default_mode"], "generate")

    def test_workflows_do_not_contain_credentials(self):
        for path in (GUI_PATH, API_PATH):
            text = path.read_text(encoding="utf-8").lower()
            for forbidden in ("fal_key=", "api_key=", "authorization:", "bearer "):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
