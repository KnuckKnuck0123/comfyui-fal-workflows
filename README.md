# ComfyUI Workflows for Architecture — Fal.ai + Gemini + Free Local

A drop-in workflow pack for [ComfyUI](https://www.comfy.org/) built for
architectural visualization: **concept sketches → photoreal renders,
text → abstract concept imagery, image → 3D, image → video, and free local
upscaling** — all driven through hosted APIs so you don't need a beefy GPU.

**Workshop-ready.** Bring your own API key, load a workflow, type a prompt,
hit **Queue**. No coding required.

![Workflow pack overview — 27 architectural workflows in the ComfyUI sidebar](docs/img/hero.png)

*(add a screenshot of your ComfyUI sidebar with the workflows loaded — see `docs/img/README.md`)*

---

## For workshop students — start here

You need three things before the workshop:

1. **ComfyUI installed and running** on your machine. Your instructor will
   provide the install checklist. Verify by opening `http://127.0.0.1:8188`
   in your browser and seeing the ComfyUI canvas.
2. **A Fal.ai API key.** Free to sign up, credit-card required, you get a
   small starter balance. [Instructions below.](#step-1-get-a-falai-api-key)
3. **These workflows loaded into your ComfyUI.** [Copy them in.](#step-3-load-the-workflows-into-comfyui)

Total setup time: ~10 minutes.

---

## Step 1: Get a Fal.ai API key

1. Go to **[fal.ai](https://fal.ai/)** and click **Sign up**.
2. Once logged in, click your avatar (top-right) → **Dashboard** → **Keys**
   (direct link: [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)).
3. Click **Add key**, name it something like `comfyui-workshop`, copy the
   key that appears. **You will only see it once — save it somewhere safe.**
4. Add **at least $5** of credit under **Billing** — this will comfortably
   cover a 2–3 hour workshop for one person.

### Cost expectations (rough, per generation)

| What you're making | Model | Approx. cost |
|---|---|---|
| Text → abstract image | Flux Dev | ~$0.025 |
| Sketch → photoreal render | Flux Pro Kontext | ~$0.05 |
| Image → 3D model | Trellis / Meshy | ~$0.10–0.40 |
| Text → video (5 sec) | Seedance / Veo3 | ~$0.20–1.50 |
| Local upscale | ESRGAN | **Free** |

A student burning through 50 renders + 10 upscales in a workshop typically
spends **under $3**. Video and 3D are the expensive tracks.

### Optional: Google Gemini key (Nano Banana workflows)

If you want to try the Nano Banana refinement workflows, also grab a free
Gemini key at **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.
Not required for the main workshop track.

---

## Step 2: Give ComfyUI your API key

The `fal-api` custom node reads `FAL_KEY` from your environment. Set it
**before** starting ComfyUI:

### Windows (PowerShell)

Persistent (survives reboots) — recommended:
```powershell
setx FAL_KEY "paste-your-fal-key-here"
# Close and reopen PowerShell + ComfyUI for it to take effect.
```

Or just for the current session:
```powershell
$env:FAL_KEY = "paste-your-fal-key-here"
```

### macOS / Linux

Persistent — add to `~/.zshrc` (macOS default) or `~/.bashrc`:
```bash
export FAL_KEY=paste-your-fal-key-here
```
Then `source ~/.zshrc` (or open a new terminal) and launch ComfyUI from that shell.

### Optional (Gemini)
```powershell
setx GEMINI_API_KEY "paste-your-gemini-key-here"    # Windows
export GEMINI_API_KEY=paste-your-gemini-key-here    # macOS/Linux
```

**Restart ComfyUI** after setting keys so it picks up the new environment.

---

## Step 3: Load the workflows into ComfyUI

1. **Download this repo** — click the green **Code** button on GitHub →
   **Download ZIP** — or if you have git:
   ```bash
   git clone https://github.com/<your-org>/comfyui-fal-workflows.git
   ```

2. **Copy the `workflows_gui/*.json` files** into your ComfyUI's user
   workflows folder so they appear in the sidebar:

   **Windows (ComfyUI Desktop):**
   ```
   C:\Users\<you>\Documents\ComfyUI\user\default\workflows\
   ```

   **Windows (portable ComfyUI):**
   ```
   <ComfyUI-folder>\user\default\workflows\
   ```

   **macOS:**
   ```
   ~/Documents/ComfyUI/user/default/workflows/
   ```

3. **Restart ComfyUI.** Open the **Workflows** panel in the left sidebar —
   you'll see all 27 workflows.

4. **Install the required custom nodes.** In ComfyUI, open **Manager** →
   **Custom Nodes Manager** → search for and install:
   - `fal-api` (required for every workflow except `upscale_local*`)
   - `nanobananaapi` (only if you got a Gemini key)

   Restart ComfyUI one more time after installing.

---

## Step 4: Make your first image

Try these three, in order, to get a feel for the pack:

### 1. `abstract_flux` — text to image (cheapest, no image needed)

1. Click `abstract_flux` in the Workflows sidebar.
2. In the **Flux Dev (fal)** node, edit the `prompt` field. Example:
   > `brutalist library atrium at dusk, warm rim light, architectural photography, editorial magazine style`
3. Click **Queue**. First run: ~10–20 seconds. Result lands in the Save Image node preview and in `ComfyUI/output/`.

### 2. `render_kontext` — sketch to photoreal render

1. Click `render_kontext` in the sidebar.
2. In the **Load Image** node, upload a sketch, massing screenshot, or
   Rhino/Revit viewport grab.
3. In the **Flux Pro Kontext (fal)** node, prompt something like:
   > `photoreal architectural render, glass and concrete facade, overcast afternoon light, people at street level, editorial style`
4. Click **Queue**. ~20–40 seconds.

### 3. `upscale_local` — free 4× upscale (no API cost)

1. Requires a local upscale model. Download an ESRGAN `.pth` (e.g.
   [RealESRGAN_x4plus.pth](https://github.com/xinntao/Real-ESRGAN/releases))
   and drop it in `ComfyUI/models/upscale_models/`.
2. Click `upscale_local`, upload the image you just rendered, hit **Queue**.
3. Free, local, no API traffic.

---

## The full workflow catalog

All 27 workflows, grouped by what they do. See
[`docs/WORKFLOWS.md`](docs/WORKFLOWS.md) for parameter tables and full
per-workflow details.

### Concept / abstract (text → image)
- `abstract_flux` — Flux Dev, balanced quality/cost. **← start here**
- `abstract_krea` — Krea 2 / FLUX.1 Krea, aesthetic-focused
- `abstract_generic_fal` — swap any Fal text-to-image endpoint
- `abstract_multigen` — one prompt → N variations, Midjourney-style
- `abstract_i2i` — image-to-image restyle

### Render (image → photoreal)
- `render_kontext` — Flux Pro Kontext, best structure preservation. **← start here**
- `render_nanobanana_gemini` — Google Nano Banana (Gemini key)
- `render_generic_fal` — swap any Fal edit endpoint
- `render_then_upscale` — render + free local upscale in one pass

### Refine (iterative edits)
- `refine_from_output` — pick any output image, refine with a new prompt (Gemini)
- `refine_from_output_generic` — same, but through any Fal endpoint
- `refine_nanobanana_chain` — 3-stage Nano Banana refinement chain
- `refine_multi_engine_chain` — Kontext → Fal edit → Nano Banana, 3-stage

### Upscale
- `upscale_local` — free ESRGAN, local GPU. **← start here**
- `upscale_local_to_target` — free ESRGAN + resize to exact WxH
- `upscale_clarity` — paid Fal Clarity (adds invented detail)
- `upscale_topaz` — paid Fal Topaz (highest-end)

### 3D (image → .glb model)
- `3d_image_to_glb_trellis` — Trellis 2, fast general-purpose
- `3d_image_to_glb_meshy` — Meshy v6, textured meshes
- `3d_image_to_glb_rodin` — Hyper3D Rodin, organic shapes
- `3d_generic_fal` — swap any Fal image-to-3D endpoint

### Video (text or image → video)
- `video_text_to_video` — Seedance 2.0 text-to-video
- `video_veo3_text` — Google Veo3 (best quality, includes audio)
- `video_image_to_video` — Seedance image + motion prompt
- `video_kling_image` — Kling Pro 1.6 image + motion prompt
- `video_generic_fal` — swap any Fal video endpoint
- `video_preview_from_url` — utility: preview a hosted video URL

---

## Troubleshooting

**"Fal API returned 401 / Unauthorized"**
Your `FAL_KEY` isn't set in the environment ComfyUI is running in. Close
ComfyUI, verify with `echo $env:FAL_KEY` (PowerShell) or `echo $FAL_KEY`
(bash), then relaunch ComfyUI **from that same terminal**.

**"Fal API returned 402 / Insufficient credit"**
Add credit at [fal.ai/dashboard/billing](https://fal.ai/dashboard/billing).

**"Node type 'FluxDev_fal' not found"** (or `FalGenericAPI`, `FluxProKontext_fal`, etc.)
The `fal-api` custom node isn't installed. Open ComfyUI Manager → install
`fal-api` → restart ComfyUI.

**"Node type 'NanoBanana API🍌' not found"**
Install `nanobananaapi` via ComfyUI Manager.

**"Local upscale model 'RealESRGAN_x4plus.pth' not found"**
Download it (see Step 4.3) and place it in `ComfyUI/models/upscale_models/`.
Restart ComfyUI so it re-scans the folder.

**Workflow queued but nothing happens for minutes**
Video and 3D jobs take 1–5 minutes. Check the terminal running ComfyUI for
the Fal request URL and progress. If nothing appears there either, verify
your key and your Fal credit balance.

**Empty / blank image output on Nano Banana workflows**
Your `GEMINI_API_KEY` isn't set, or the prompt tripped Gemini's safety
filter. Check the ComfyUI terminal for errors.

---

## Advanced: the CLI runner (`run_fal_workflow.py`)

If you're comfortable in a terminal, `run_fal_workflow.py` lets you drive
the same workflows from the command line — useful for batching, scripting,
and letting an AI agent (Claude Code, Cursor, GPT, etc.) run them for you.

```powershell
# Point the runner at your ComfyUI install
$env:COMFY_ROOT = "C:\Users\<you>\Documents\ComfyUI"

# List every workflow with cost + swappable model info
python run_fal_workflow.py --list

# Text-to-image
python run_fal_workflow.py abstract_flux --prompt "brutalist library atrium at dusk"

# Sketch to render
python run_fal_workflow.py render_kontext --image shot.png --prompt "photoreal dusk render"

# Free local upscale
python run_fal_workflow.py upscale_local --image render.png
```

The runner auto-starts ComfyUI if it isn't already listening on
`127.0.0.1:8188`, preflights your auth env vars, injects params into the
API-format workflow JSON, and prints the output paths.

Full CLI reference: [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md).
Agent context file: [`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md).

---

## Repo layout

```
comfyui-fal-workflows/
├── workflows_gui/           27 workflow JSONs for the ComfyUI browser UI (drag or copy)
├── workflows_api/           27 workflow JSONs for the CLI runner / agents (API format)
├── run_fal_workflow.py      CLI runner (optional, power-user)
├── fal_models.json          Workflow registry (metadata for the runner)
├── docs/
│   ├── WORKFLOWS.md         Full workflow reference — parameters, swappable engines
│   ├── AI_AGENT_GUIDE.md    Loadable context for AI agents
│   └── fal-links.txt        Fal endpoint reference links
├── .env.example             Auth template
├── requirements.txt         Extra Python deps (for the CLI runner)
└── LICENSE                  MIT
```

`workflows_gui/` and `workflows_api/` are functionally identical — just
different formats. The GUI ones show up in ComfyUI's sidebar; the API ones
are what the runner and agents inject prompts into.

---

## What's NOT in this repo

- **ComfyUI itself** — install from [comfy.org](https://www.comfy.org/) or [GitHub](https://github.com/comfyanonymous/ComfyUI).
- **The custom nodes** (`fal-api`, `nanobananaapi`) — install via ComfyUI Manager.
- **Model weights** (`.pth`, `.safetensors`) — bring your own.
- **Your API keys** — never commit them.

---

## License

MIT — see [LICENSE](LICENSE). Fork it, adapt it for your studio or course.
