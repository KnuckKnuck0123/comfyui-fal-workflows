import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "workflows_gui"
API = ROOT / "workflows_api"
REGISTRY = ROOT / "fal_models.json"

REMOVED_REDUNDANCIES = (
    "video_text_to_video",
    "video_image_to_video",
    "nanobanana_2_edit",
    "nanobanana_pro_edit",
    "nanobanana_2_inpaint",
    "nanobanana_pro_inpaint",
    "abstract_flux",
)


class WorkflowConsolidationTests(unittest.TestCase):
    def test_redundant_workflows_are_removed_from_both_formats_and_registry(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["workflows"]
        for name in REMOVED_REDUNDANCIES:
            with self.subTest(workflow=name):
                self.assertFalse((GUI / f"{name}.json").exists())
                self.assertFalse((API / f"{name}.json").exists())
                self.assertNotIn(name, registry)

    def test_canonical_replacements_remain_available(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["workflows"]
        for name in ("video_studio_fal", "nanobanana_edit_inpaint", "abstract_generic_fal", "3d_generic_fal"):
            with self.subTest(workflow=name):
                self.assertTrue((GUI / f"{name}.json").is_file())
                self.assertTrue((API / f"{name}.json").is_file())
                self.assertIn(name, registry)


if __name__ == "__main__":
    unittest.main()
