"""Remove workflow files replaced by canonical consolidated workspaces."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOVED = (
    "video_text_to_video",
    "video_image_to_video",
    "nanobanana_2_edit",
    "nanobanana_pro_edit",
    "nanobanana_2_inpaint",
    "nanobanana_pro_inpaint",
    "abstract_flux",
)


def main():
    for folder in (ROOT / "workflows_gui", ROOT / "workflows_api"):
        for name in REMOVED:
            path = folder / f"{name}.json"
            if path.exists():
                path.unlink()

    registry_path = ROOT / "fal_models.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for name in REMOVED:
        registry["workflows"].pop(name, None)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
