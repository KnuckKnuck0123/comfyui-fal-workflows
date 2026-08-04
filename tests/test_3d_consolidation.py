import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "workflows_gui"
API = ROOT / "workflows_api"
REGISTRY = ROOT / "fal_models.json"
NODE_HELPERS = ROOT.parent / "Comfy" / "ComfyUI" / "custom_nodes" / "fal-api" / "nodes"
LEGACY = (
    "3d_image_to_glb_trellis",
    "3d_image_to_glb_meshy",
    "3d_image_to_glb_rodin",
)
MODELS = [
    "fal-ai/trellis-2",
    "fal-ai/meshy/v6/image-to-3d",
    "fal-ai/meshy/v6/multi-image-to-3d",
    "fal-ai/hyper3d/rodin/v2.5",
    "fal-ai/pixal3d",
    "fal-ai/hunyuan_world/image-to-world",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_helper(name):
    path = NODE_HELPERS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImageTo3DConsolidationTests(unittest.TestCase):
    def test_one_canonical_workflow_replaces_model_specific_duplicates(self):
        self.assertTrue((GUI / "3d_generic_fal.json").is_file())
        self.assertTrue((API / "3d_generic_fal.json").is_file())
        registry = load_json(REGISTRY)["workflows"]
        self.assertEqual(registry["3d_generic_fal"]["swappable_values"], MODELS)
        for name in LEGACY:
            self.assertFalse((GUI / f"{name}.json").exists())
            self.assertFalse((API / f"{name}.json").exists())
            self.assertNotIn(name, registry)

    def test_canonical_workflow_accepts_a_second_view(self):
        graph = load_json(API / "3d_generic_fal.json")
        loads = [node for node in graph.values() if node.get("class_type") == "LoadImage"]
        self.assertEqual(len(loads), 2)
        engine = next(node for node in graph.values() if node.get("class_type") == "FalGenericAPI")
        self.assertEqual(engine["inputs"]["endpoint"], "fal-ai/trellis-2")
        self.assertIn("image_2", engine["inputs"])

    def test_3d_endpoints_receive_their_schema_specific_image_fields(self):
        mapper = load_helper("endpoint_image_arguments")
        self.assertEqual(
            mapper.map_uploaded_images("fal-ai/trellis-2", ["one", "two"]),
            {"image_url": "one"},
        )
        self.assertEqual(
            mapper.map_uploaded_images("fal-ai/meshy/v6/multi-image-to-3d", ["one", "two"]),
            {"image_urls": ["one", "two"]},
        )
        self.assertEqual(
            mapper.map_uploaded_images("fal-ai/hyper3d/rodin/v2.5", ["one", "two"]),
            {"image_urls": ["one", "two"]},
        )

    def test_3d_result_urls_are_extracted_for_shared_output(self):
        helper = load_helper("endpoint_result_url")
        self.assertEqual(helper.extract_asset_url({"model_glb": {"url": "trellis.glb"}}), "trellis.glb")
        self.assertEqual(helper.extract_asset_url({"model_mesh": {"url": "rodin.glb"}}), "rodin.glb")
        self.assertEqual(helper.extract_asset_url({"world_file": {"url": "scene.world"}}), "scene.world")


if __name__ == "__main__":
    unittest.main()
