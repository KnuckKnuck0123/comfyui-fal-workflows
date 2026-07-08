# comfyui-fal-workflows

Agent-driven ComfyUI workflows that route image, video, and 3D generation
through **Fal.ai**, **Google Gemini (Nano Banana)**, and **free local GPU
upscaling** — with a single CLI runner that any AI agent (Claude, GPT, Gemini,
Cursor, etc.) can drive.

Built for architectural visualization: abstract concepts, rendered elevations,
Kontext-style edits, refine chains, batched upscale, and text/image-to-video.

---

## Contents

| Path | Purpose |
|---|---|
| `workflows_fal/` | 27 API-format ComfyUI workflow JSONs |
| `run_fal_workflow.py` | CLI runner — auto-starts ComfyUI, injects params, polls, saves |
| `fal_models.json` | Workflow registry: friendly names, auth, swappable engines/models |
| `docs/WORKFLOWS.md` | Full human-facing workflow reference |
| `docs/AI_AGENT_GUIDE.md` | Loadable context for AI agents driving the runner |
| `docs/fal-links.txt` | Fal endpoint reference links |
| `.env.example` | Auth template (`FAL_KEY`, `GEMINI_API_KEY`) |
| `requirements.txt` | Extra Python deps for the ComfyUI custom nodes |

---

## Prerequisites

1. A working **ComfyUI** install (Desktop or portable). Tested against ComfyUI
   with a `.venv` inside the `ComfyUI/` folder.
2. These ComfyUI custom nodes:
   - **fal-api** — provides `FalGenericAPI`, `FluxProKontext_fal`, `FluxDev_fal`, etc.
   - **nanobananaapi** — provides `NanoBanana API🍌` (Gemini image editing)
3. A Fal.ai account with credits (for any workflow with `auth: "fal"`).
4. A Google AI Studio API key (for Nano Banana workflows).
5. Optional: any ESRGAN-family `.pth` file dropped in `ComfyUI/models/upscale_models/`
   for free local upscaling.

---

## Install

The runner assumes it lives **at the same level as your `ComfyUI/` folder**
(i.e. `<comfy_root>/run_fal_workflow.py` and `<comfy_root>/ComfyUI/main.py`).

```powershell
# From your ComfyUI install root:
git clone https://github.com/<you>/comfyui-fal-workflows.git .tmp-fal
Copy-Item .tmp-fal\run_fal_workflow.py .
Copy-Item .tmp-fal\fal_models.json .
Copy-Item -Recurse .tmp-fal\workflows_fal ComfyUI\workflows_fal
Remove-Item -Recurse -Force .tmp-fal
```

Or clone the whole repo alongside and symlink; whatever fits your workflow.

---

## Auth

Set these in your shell environment (the runner reads them at process start —
it does **not** auto-load `.env` files):

```powershell
# Windows, persistent:
setx FAL_KEY "your-fal-key"
setx GEMINI_API_KEY "your-gemini-key"

# Windows, current session only:
$env:FAL_KEY = "your-fal-key"
$env:GEMINI_API_KEY = "your-gemini-key"
```

```bash
# macOS/Linux:
export FAL_KEY=your-fal-key
export GEMINI_API_KEY=your-gemini-key
```

Never commit real keys. `.gitignore` blocks `.env` for safety.

---

## Usage

```powershell
# List every workflow with cost + swappable model/endpoint info
python run_fal_workflow.py --list

# Text-to-image, default engine
python run_fal_workflow.py abstract_flux --prompt "brutalist library atrium at dusk"

# Image edit with Fal FLUX Kontext
python run_fal_workflow.py render_kontext --image shot.png --prompt "photoreal dusk render, glass facade"

# Swap the Fal endpoint on a generic workflow
python run_fal_workflow.py render_generic_fal --image sketch.jpg --prompt "..." --endpoint fal-ai/flux-2/edit

# Free local upscale
python run_fal_workflow.py upscale_local --image render.png

# Opt into a paid API upscaler instead
python run_fal_workflow.py upscale_local --image render.png --paid clarity
```

The runner will:

1. Auto-start ComfyUI on `127.0.0.1:8188` if it is not already listening.
2. Preflight-check the required auth env vars.
3. Stage the input image into `ComfyUI/input/` with a unique name.
4. Inject prompt/image/endpoint/seed/extra into the workflow JSON.
5. Queue the prompt via `POST /prompt`, poll `/history/<id>`, and print the
   output paths under `ComfyUI/output/`.

Full CLI reference and per-workflow parameter tables are in
[`docs/WORKFLOWS.md`](docs/WORKFLOWS.md).

---

## Driving from an AI agent

Load [`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md) as agent context. It
documents:

- All 27 workflows and their swappable fields.
- Cost/auth model per workflow (local vs Fal vs Gemini).
- Recommended prompt patterns for architectural output.
- Failure modes and how to recover.

---

## What's NOT in this repo

- ComfyUI itself — install separately from https://github.com/comfyanonymous/ComfyUI
- The `fal-api` and `nanobananaapi` custom nodes — install via ComfyUI Manager.
- Model weights (`.pth`, `.safetensors`) — bring your own.
- Generated `output/` and `input/` folders.
- API keys.

---

## License

MIT — see [LICENSE](LICENSE).
