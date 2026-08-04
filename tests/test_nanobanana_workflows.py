import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from run_fal_workflow import inject_params


ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = ROOT / "workflows_gui"
API_DIR = ROOT / "workflows_api"
REGISTRY_PATH = ROOT / "fal_models.json"

EXPECTED = {
    "nanobanana_2_generate": {"model": "Nano Banana 2", "needs_image": False},
    "nanobanana_pro_generate": {"model": "Nano Banana Pro", "needs_image": False},
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class NanoBananaWorkflowContractTests(unittest.TestCase):
    def test_unified_edit_inpaint_workflow_is_model_swappable(self):
        name = "nanobanana_edit_inpaint"
        self.assertTrue((GUI_DIR / f"{name}.json").is_file())
        self.assertTrue((API_DIR / f"{name}.json").is_file())

        registry = load_json(REGISTRY_PATH)["workflows"][name]
        self.assertEqual(registry["swappable_field"], "model")
        self.assertEqual(
            registry["swappable_values"],
            ["Nano Banana 2", "Nano Banana Pro"],
        )

    def test_runner_model_override_updates_official_nano_banana_node(self):
        workflow = {
            "1": {
                "class_type": "NanoBananaGeminiImageNode",
                "inputs": {"model": "Nano Banana 2"},
            }
        }
        args = SimpleNamespace(
            workflow="nanobanana_edit_inpaint",
            image=None,
            prompt=None,
            seed=None,
            endpoint=None,
            model="Nano Banana Pro",
            extra=None,
            filename_prefix=None,
        )
        patched = inject_params(workflow, args, {"needs_image": False})
        self.assertEqual(patched["1"]["inputs"]["model"], "Nano Banana Pro")

    def test_four_base_workflows_exist_in_gui_and_api_formats(self):
        for name in EXPECTED:
            with self.subTest(workflow=name):
                self.assertTrue((GUI_DIR / f"{name}.json").is_file())
                self.assertTrue((API_DIR / f"{name}.json").is_file())

    def test_api_workflows_use_dedicated_node_models_and_edit_connections(self):
        for name, expected in EXPECTED.items():
            with self.subTest(workflow=name):
                graph = load_json(API_DIR / f"{name}.json")
                nodes = list(graph.values())
                nano_nodes = [
                    node
                    for node in nodes
                    if node.get("class_type") == "NanoBananaGeminiImageNode"
                ]
                self.assertEqual(len(nano_nodes), 1)
                inputs = nano_nodes[0]["inputs"]
                self.assertEqual(inputs["model"], expected["model"])
                self.assertEqual("images" in inputs, expected["needs_image"])
                self.assertEqual(inputs["prompt"], "PARAM_PROMPT")

    def test_gui_workflows_use_dedicated_node_models_and_edit_connections(self):
        for name, expected in EXPECTED.items():
            with self.subTest(workflow=name):
                graph = load_json(GUI_DIR / f"{name}.json")
                nano_nodes = [
                    node
                    for node in graph["nodes"]
                    if node.get("type") == "NanoBananaGeminiImageNode"
                ]
                self.assertEqual(len(nano_nodes), 1)
                node = nano_nodes[0]
                self.assertEqual(node["widgets_values"][1], expected["model"])
                image_inputs = [item for item in node.get("inputs", []) if item["name"] == "images"]
                self.assertEqual(bool(image_inputs and image_inputs[0].get("link")), expected["needs_image"])

    def test_no_workflow_uses_legacy_nanobanana_node(self):
        legacy = "NanoBanana API\U0001f34c"
        offenders = []
        for folder in (GUI_DIR, API_DIR):
            for path in folder.glob("*.json"):
                graph = load_json(path)
                if legacy in json.dumps(graph, ensure_ascii=False):
                    offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_registry_contains_four_base_workflows(self):
        registry = load_json(REGISTRY_PATH)["workflows"]
        for name, expected in EXPECTED.items():
            with self.subTest(workflow=name):
                self.assertIn(name, registry)
                self.assertEqual(registry[name]["file"], f"{name}.json")
                self.assertEqual(registry[name]["needs_image"], expected["needs_image"])
                self.assertEqual(registry[name]["auth"], "gemini")

    def test_registry_does_not_advertise_legacy_nanobanana_node(self):
        registry = load_json(REGISTRY_PATH)["workflows"]
        offenders = {
            name: meta.get("engine_node", "")
            for name, meta in registry.items()
            if "NanoBanana API" in meta.get("engine_node", "")
        }
        self.assertEqual(offenders, {})

    def test_inpaint_workflows_explain_semantic_masking(self):
        required_phrase = "change only"
        for name in ("nanobanana_edit_inpaint",):
            with self.subTest(workflow=name):
                api_graph = load_json(API_DIR / f"{name}.json")
                nano_node = next(
                    node
                    for node in api_graph.values()
                    if node.get("class_type") == "NanoBananaGeminiImageNode"
                )
                self.assertIn(required_phrase, nano_node["inputs"]["system_prompt"].lower())

                registry = load_json(REGISTRY_PATH)["workflows"][name]
                self.assertEqual(registry["edit_mode"], "semantic_masking")


if __name__ == "__main__":    unittest.main()
