# Fal / Gemini / Local Upscale ComfyUI Workflows

Rendering workflows that run **locally through your ComfyUI instance** and only
call out to model APIs for the paid steps. Upscaling is **free by default**
(local GPU).

Two ways to run them:

- **In the ComfyUI web UI** (graph editor, click Run) - `ComfyUI/user/default/workflows/*.json` (UI format, visible in the Workflows sidebar)
- **From the CLI / an AI agent** - `run_fal_workflow.py` + `ComfyUI/workflows_fal/*.json` (API format)

Both sets do the exact same thing; use whichever fits the task.

Other files:

- Registry: `fal_models.json` (friendly names, auth, swappable engines - CLI only)
- Outputs land in `ComfyUI/output/`

## Using the workflows in the ComfyUI UI

1. Start ComfyUI. Make sure `FAL_KEY` and (if using Nano Banana) `GEMINI_API_KEY` are set in the environment *before* ComfyUI launches - the custom nodes read them at startup.
2. Open the ComfyUI web UI, open the **Workflows** sidebar (left side).
3. You will see the 26 workflows under `default/workflows/`. Click to load.
4. Every workflow starts with placeholder values you should edit before running:
   - `LoadImage` nodes point to `example.png` - swap for your real input via the widget.
   - The prompt widget in the engine node holds a default architectural prompt - replace it.
   - Fal generic/abstract workflows: the `endpoint` widget is a dropdown. Common values (verified live on fal.ai):
     - **Screenshot/sketch/i2i edit:** `openai/gpt-image-2/edit`, `fal-ai/gpt-image-1.5/edit`, `fal-ai/flux-2/edit`, `fal-ai/flux-2-pro/edit`, `fal-ai/flux-2-max/edit`, `fal-ai/flux-pro/kontext`, `fal-ai/flux-pro/kontext/max`, `fal-ai/flux-kontext/dev`, `fal-ai/bytedance/seedream/v4.5/edit`, `fal-ai/bytedance/seedream/v5/lite/edit`, `xai/grok-imagine-image/quality/edit`, `fal-ai/qwen-image-edit-2511-multiple-angles`
     - **Abstract text-to-image:** `fal-ai/z-image/turbo`, `ideogram/v4`, `fal-ai/flux-2`, `fal-ai/flux-2/turbo`, `fal-ai/flux-2-pro`, `fal-ai/flux-pro/v1.1-ultra`, `openai/gpt-image-2`, `xai/grok-imagine-image`
     - **Krea (aesthetic):** `krea/v2/large/text-to-image` (best quality), `krea/v2/medium/text-to-image` (balanced), `krea/v2/medium/turbo/text-to-image` (fast), `fal-ai/krea-2/turbo` (newer)
     - **Nano Banana `model` (Gemini key path, live 2026-07 IDs):** `gemini-3.1-flash-image` (Nano Banana 2, default), `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite, cheaper), `gemini-3-pro-image` (Nano Banana Pro, top-tier), `gemini-2.5-flash-image` (original Nano Banana). The `-preview` suffix from earlier IDs is deprecated; use the plain names above. To list what your key can access: `curl "https://generativelanguage.googleapis.com/v1beta/models?key=$env:GEMINI_API_KEY"`.
5. Click **Run** (or Queue). Outputs land in `ComfyUI/output/` with the `filename_prefix` set on the SaveImage node.

Notes:
- If a workflow does not appear after adding files, click the refresh icon in the ComfyUI Workflows sidebar, or restart ComfyUI Desktop.
- Local upscale needs a `.pth` in `ComfyUI/models/upscale_models/` (see below).
- The UI-format files live in `<ComfyUI>/user/default/workflows/` (this repo's `workflows_gui/`). The API-format twins in this repo's `workflows_api/` are for the CLI runner and are not shown in the UI sidebar.
- The `FalGenericAPI` endpoint dropdown was refreshed against the live fal.ai catalog. If you add newer endpoints, either edit `custom_nodes/fal-api/nodes/generic_node.py` (`FAL_ENDPOINTS` list) and restart ComfyUI, or type the endpoint string directly into the workflow JSON - the frontend accepts any string, not just dropdown entries.

### Fast workflow chooser

- New image from text: `abstract_generic_fal`
- Sketch/viewport to render: `render_kontext`
- Gemini edit or semantic inpaint: `nanobanana_edit_inpaint`
- Text/image/first-last/reference video: `video_studio_fal`
- Single/multi-view image to 3D: `3d_generic_fal`
- Free local upscale: `upscale_local`

## Workflow catalog (UI + CLI)

| Workflow | Cost | What it does | Default engine |
|---|---|---|---|
| `content_engine_image_studio` | Fal | Unified hosted Generate, Edit / Render, Variations, and Upscale workspace with lazy routing. | FalGenericAPI |
| `nanobanana_2_generate` | Gemini | Nano Banana 2 text-to-image generation. | NanoBananaGeminiImageNode |
| `nanobanana_pro_generate` | Gemini | Nano Banana Pro text-to-image generation. | NanoBananaGeminiImageNode |
| `refine_nanobanana_chain` | Gemini | Gemini-style multi-stage refinement (3 chained Nano Banana passes) | NanoBanana x3 |
| `refine_from_output` | Gemini | pick a prior output + refine prompt (interactive loop) | NanoBanana |
| `refine_multi_engine_chain` | Fal + Gemini | 3-stage refinement across different engines | Kontext -> any Fal /edit -> Nano Banana |
| `refine_from_output_generic` | Fal | interactive refinement loop via any Fal /edit model | FalGenericAPI |
| `render_kontext` | Fal | screenshot/sketch -> photoreal render | FluxProKontext_fal |
| `render_nanobanana_gemini` | Gemini | screenshot/sketch -> render (official Google) | NanoBanana (Gemini key) |
| `render_generic_fal` | Fal | screenshot/sketch -> render, swappable engine | `openai/gpt-image-2/edit` |
| `abstract_generic_fal` | Fal | text-to-image abstract, swappable engine | `fal-ai/z-image/turbo` |
| `abstract_krea` | Fal | text-to-image via Krea 2 family | `krea/v2/large/text-to-image` |
| `abstract_multigen` | Fal | Midjourney-style: one prompt -> N variations, model-swappable | `fal-ai/flux-2` |
| `abstract_i2i` | Fal | image-to-image abstract restyle | `fal-ai/flux-2/edit` |
| `upscale_local` | FREE | local GPU ESRGAN 4x + resize to N megapixels | `ImageUpscaleWithModel + ImageScaleToTotalPixels` |
| `upscale_local_to_target` | FREE | local GPU ESRGAN 4x + resize to exact WxH | `ImageUpscaleWithModel + ImageResizeKJv2` |
| `upscale_clarity` | Fal | paid Clarity upscaler (adds detail) | Upscaler_fal |
| `upscale_topaz` | Fal | paid Topaz upscaler (max quality) | `fal-ai/topaz/upscale/image` |
| `render_then_upscale` | Fal | Fal render + free local upscale | Kontext + local |

## Resolution: what's possible and how to control it

### Input vs output resolution

Feeding a high-res image into an edit workflow **does** help — most diffusion models downscale internally to ~1MP (~1024px) for processing, but they use your high-res input to *read* detail (linework, materials, small features) before generating. What comes out is capped by the model's max output resolution, not your input.

Recommended pipeline:
1. Generate at the model's native max (usually 2K-class; Seedream can do native 4K).
2. Upscale locally 2-4x with `upscale_local` (free, tile-safe on a 12GB RTX 5070).

That gets you 4K-8K deliverables at essentially only the initial API cost.

### Per-model output resolution limits

| Model / endpoint | Max native output | Control field |
|---|---|---|
| `fal-ai/flux-2`, `fal-ai/flux-2/turbo`, `fal-ai/flux-2-pro`, `fal-ai/flux-2-max` | 512-2048 per side | `image_size` enum or `{width,height}` |
| `fal-ai/flux/schnell`, `fal-ai/flux/dev` | up to 1536 | `image_size` |
| `fal-ai/flux-pro/v1.1` | up to 1440 | `image_size` |
| `fal-ai/flux-pro/v1.1-ultra` | up to ~2K (4MP) | `aspect_ratio` |
| `fal-ai/bytedance/seedream/v4/text-to-image`, `v4.5/text-to-image` | **up to 4096 (native 4K)** | `image_size` |
| `fal-ai/bytedance/seedream/v4/edit`, `v4.5/edit` | **up to 4096 (4K)** | `image_size` |
| `krea/v2/*`, `fal-ai/flux/krea` | ~1MP class | `image_size` / `aspect_ratio` |
| Nano Banana / Gemini image models | ~1024 (fixed-ish) | `aspect_ratio` |
| `fal-ai/ideogram/v3`, `ideogram/v4` | up to 2048 | `image_size` |
| `fal-ai/recraft/v4/pro/text-to-image` | up to 2048 | `image_size` |

### Controlling resolution in the `FalGenericAPI` workflows

The node's UI only exposes `aspect_ratio`. To set explicit resolution, use the **`extra_arguments`** JSON widget. Recipes:

- Explicit 2K widescreen:
  ```json
  {"image_size": {"width": 2048, "height": 1152}}
  ```
- Seedream native 4K:
  ```json
  {"image_size": {"width": 3840, "height": 2160}}
  ```
- Multi-gen + explicit size:
  ```json
  {"num_images": 4, "image_size": {"width": 2048, "height": 1152}}
  ```
- Preset enum (works on most Flux/Krea/Recraft):
  ```json
  {"image_size": "landscape_16_9"}
  ```
  Valid presets: `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`.

The **typed `_fal` nodes** (`FluxDev_fal`, `Recraft_fal`, `SeedreamV4Edit_fal`, etc.) have width/height widgets directly — no `extra_arguments` needed.

## Multi-gen (Midjourney-style)

`abstract_multigen` — one prompt, N image variations, side-by-side in Preview.

How it works: the `FalGenericAPI` node stacks all returned images into a batch tensor. `SaveImage` writes each one to `output/` as a separate file; `PreviewImage` shows them in a grid.

Usage:
1. Open `abstract_multigen` from the Workflows sidebar.
2. Type your prompt in the `FalGenericAPI` prompt widget.
3. (Optional) Change `endpoint` to any text-to-image model (see swap list in `fal_models.json`).
4. (Optional) Edit `extra_arguments` to control count and size, e.g. `{"num_images": 6}` or `{"num_images": 4, "image_size": "landscape_16_9"}`.
5. Click Queue Prompt. The preview shows all variations; each is also in `output/` with the `abstract_multigen` prefix.

Great for A/B testing models on the same prompt: run it with `fal-ai/flux-2`, then swap to `krea/v2/large/text-to-image`, run again, compare.

## Video and 3D workflows

These use Fal's video and 3D endpoints. **Output behavior is different from image workflows:** Fal returns a URL (mp4 or glb file). The workflows save that URL to a `.txt` file in `output/` so you have a permanent record.

### Video workflows

| Workflow | Model | Kind | Notes |
|---|---|---|---|
| `video_studio_fal` | Seedance 2.0 | text/image/first-last/reference -> video | Lazy-routed modes |
| `video_veo3_text` | Google Veo3 | text -> video | Highest quality + native audio, 8s fixed |
| `video_kling_image` | Kling Pro 1.6 | image+text -> video | Cinematic motion, optional tail-frame control |
| `video_generic_fal` | any Fal video endpoint | swappable | Test Kling/Seedance/Veo/Wan/Hailuo with one graph |
| `video_preview_from_url` | LoadVideoURL | utility | Paste any video URL to preview frames in-UI |

**How to view the generated video:**

Every video workflow now **auto-previews the result in-graph**. When the run completes, the `PreviewImage` node on the right shows a grid of ~30 frames sampled from the video (every 4th frame for 5s clips, every 6th for Veo3's 8s clips). The video URL is also saved to a `.txt` file in `output/` so you have a permanent record.

To view the actual mp4:
1. Open the `.txt` file in `output/` (e.g. `video_seedance_i2v_00001_.txt`), copy the URL, paste into any browser.
2. OR: right-click any frame in the PreviewImage node → Save Image / Open Image to grab that frame.
3. OR: use `video_preview_from_url` standalone if you want to load a URL from a past run.

Fal video URLs typically stay live for a few days; download the mp4 to your project folder for permanent storage.

To skip the preview (save API cost of extra bandwidth on the video download): Mute (Ctrl+M) the `LoadVideoURL` node and its downstream `PreviewImage`. The URL still saves to `.txt`.

### 3D workflows

| Workflow | Model | Best for |
|---|---|---|
| `3d_generic_fal` | swappable | Trellis/Meshy/Meshy Multi/Rodin/Pixal3D/Hunyuan World |

The first image is used by every model. The second image is used by Meshy Multi
and Rodin as another view of the same object. The workflow saves the primary
GLB or world-asset URL to `.txt`. Hunyuan World returns a full **scene** rather
than a conventional object mesh.

### Cost warning

Video and 3D are the most expensive Fal endpoints. Rough magnitudes as of 2026-07:
- Seedance 720p 5s: ~$0.30-0.60 per clip
- Veo3 8s with audio: ~$3-6 per clip (highest)
- Kling Pro 1.6 5s: ~$0.35-0.70 per clip
- Trellis / Meshy / Rodin: ~$0.10-0.50 per model

Check `https://fal.ai/models/<endpoint>` for current pricing before batch-running.

## Iterative refinement (Gemini / AI Studio style)

Google's AI Studio "conversational" image refinement is really just: each new prompt takes the previous output as input. This system supports the same pattern via chained nodes.

Four workflows are provided:

| Workflow | Best for | Engines |
|---|---|---|
| `refine_nanobanana_chain` | 3 quick Nano Banana passes in one click | Nano Banana x3 |
| `refine_from_output` | Interactive loop, Nano Banana only | Nano Banana |
| `refine_multi_engine_chain` | Compare engines across stages | Kontext -> any Fal /edit -> Nano Banana |
| `refine_from_output_generic` | Interactive loop, ANY Fal /edit model | FalGenericAPI |

### How to use `refine_from_output` (the closest to Gemini/AI Studio)

Step-by-step:

1. **Do an initial render** using any render workflow (e.g. `render_kontext`, `render_generic_fal`, `render_nanobanana_gemini`, or `abstract_generic_fal`). This puts an image in `ComfyUI/output/`.
2. **Open the `refine_from_output` workflow** from the Workflows sidebar.
3. **Click the `LoadImageOutput` node's image widget** (the top-left node, labeled "Pick a prior output to refine"). A dropdown appears listing every image in `output/`. Pick the one you just generated.
4. **Type a targeted refinement prompt** in the Nano Banana node's prompt widget. Good prompts are scoped:
   - `"keep the composition, change the sky to warm sunset"`
   - `"make the facade material a rough concrete instead of glass"`
   - `"add dramatic atmospheric fog in the background"`
5. **Click Queue Prompt** (or press Ctrl+Enter). Watch the PreviewImage node — the refined image appears there when done, and is also saved to `output/` with the `refine_iter` prefix.
6. **To keep refining**: click the `LoadImageOutput` dropdown again, pick the *newest* output (the one you just made), change the prompt, Queue Prompt.
7. Repeat as many times as you want. Each Queue Prompt is one Gemini API call.

If a refinement drifts too far, just pick an earlier output from the dropdown and try a different prompt. No history to reset — each run is stateless.

### How to use `refine_nanobanana_chain` (one-click multi-stage)

- Load an input image (LoadImage node, leftmost).
- Each of the 3 stage nodes has its own prompt widget. Fill in the sequence you want, e.g.:
  - Stage 1: `"turn this sketch into a photoreal architectural render, dramatic lighting"`
  - Stage 2: `"change the sky to a warm sunset with subtle haze"`
  - Stage 3: `"add crisp material detail, subtle window reflections"`
- Click Queue Prompt. All three run in sequence; you see each result in the corresponding preview node.
- **Skip stages** by right-clicking a stage node and choosing Mute (or press Ctrl+M with the node selected). Downstream previews will show blank; the SaveImage will save the last un-muted stage.

### How to use `refine_multi_engine_chain` (compare models across stages)

Same as the Nano Banana chain, but each stage uses a different engine:
- Stage 1: `FluxProKontext_fal` (strong structure preservation) — good for the initial render.
- Stage 2: `FalGenericAPI` — change the `endpoint` widget to any `/edit` model to test how each handles the refinement. Try `fal-ai/flux-2/edit`, `openai/gpt-image-2/edit`, `fal-ai/bytedance/seedream/v4.5/edit`, `fal-ai/flux-pro/kontext/max`.
- Stage 3: Nano Banana — good for final polish.

### How to use `refine_from_output_generic` (interactive, any Fal model)

Same as `refine_from_output` but uses `FalGenericAPI` instead of Nano Banana, so it costs Fal credits (not Gemini) and lets you pick from any Fal `/edit` endpoint. Change the `endpoint` widget between runs to swap engines mid-refinement.

### Prompt tips for semantic inpainting

- **Anchor**: "keep everything else the same" or "same composition, same angle"
- **Scope**: "in the foreground, ..." or "on the facade, ..."
- **Avoid full re-descriptions** — those cause drift.
- Nano Banana and Flux Kontext preserve unmasked regions best. GPT-Image-2 and Seedream tend to reinterpret more.

## Using the CLI runner (agent-driven)

The runner is optional - only needed if you want to fire workflows from the command line or from an AI agent. Everything below covers that path.

## 1. Setup

### API keys (environment variables — never stored on disk)

PowerShell (current session):
```powershell
$env:FAL_KEY = "your-fal-key"
$env:GEMINI_API_KEY = "your-gemini-key"
```
Persist across sessions:
```powershell
setx FAL_KEY "your-fal-key"
setx GEMINI_API_KEY "your-gemini-key"
```

- `FAL_KEY` — needed for any workflow with cost **paid (FAL_KEY)**.
- `GEMINI_API_KEY` — needed only for `render_nanobanana_gemini`.
- Local upscale needs **no key**.

## Upscale: resolution control and artifact troubleshooting

### Resolution — what each workflow can actually do

| Workflow | Resolution control | Prompt required? |
|---|---|---|
| `upscale_local` | ESRGAN 4x fixed, then resize to N megapixels (default 8 MP) | No |
| `upscale_local_to_target` | ESRGAN 4x fixed, then resize to EXACT WxH (default 3840x2160) | No |
| `upscale_clarity` | `upscale_factor` slider 1.0-4.0 (no explicit width/height) | No - positive prompt is hardcoded in the node |
| `upscale_topaz` | Fal endpoint - use extra_arguments to set target | No |

Key facts:

- **ESRGAN models have a FIXED multiplier.** `4x-UltraSharp.pth` is always 4x. `2x_*` models are 2x. You cannot ask a 4x model to do 2x - you upscale then downscale.
- **The size widgets in `upscale_local` / `upscale_local_to_target` are on the resize node AFTER the ESRGAN pass**, not on the upscale itself. That's the correct pattern.
- **Clarity's positive prompt is baked in.** The Fal node hardcodes `"prompt": "masterpiece, best quality, highres"` internally; only the negative prompt widget affects generation.

### Fixing "images too small"

If `upscale_local` was giving you outputs the same size as the input, the old workflow ran raw 4x with no resize step and you may have been looking at the PreviewImage (which displays scaled-to-fit). The new `upscale_local` explicitly targets 8 MP (~3760x2116 at 16:9). Use `upscale_local_to_target` when you need an exact pixel size (e.g. 3840x2160, 5120x2880, 7680x4320).

To push higher than 4x from a small input: chain the workflow twice. Run `upscale_local` once (input 1024 -> ~3760), save the output, load it back and run again (3760 -> huge).

### Fixing "weird artifacts"

The three usual causes and fixes:

1. **JPEG source artifacts** get 4x-amplified. Use a PNG source if you have one, or run a mild denoise pass before upscaling.
2. **Wrong ESRGAN model for the content style.** Swap the `UpscaleModelLoader` model_name widget:
   - Renders / photoreal: `4x-UltraSharp.pth` (default) or `4x_NMKD-Siax_200k.pth`
   - Stylized / illustrated: `4x_foolhardy_Remacri.pth`
   - Anime / graphic: `4x-AnimeSharp.pth`
3. **Clarity hallucinating detail.** Lower `creativity` (I already dropped the default from 0.35 to 0.20). Raise `resemblance` (default now 0.75) if it still drifts. If it's still noisy, drop `guidance_scale` toward 2.5.

### `upscale_local` in detail

Graph: `LoadImage -> UpscaleModelLoader -> ImageUpscaleWithModel (4x) -> ImageScaleToTotalPixels -> SaveImage + Preview`.

The `ImageScaleToTotalPixels` node has three widgets:
- `upscale_method` - `lanczos` recommended for downscale-from-4x
- `megapixels` - target output size in MP. Reference: 2 MP = ~1920x1080, 8 MP = ~3760x2116, 12 MP = ~4600x2592, 33 MP = 7680x4320 (8K UHD).
- `resolution_steps` - rounds output dims to multiples of this (64 keeps things model-friendly for later diffusion steps).

**Mute (Ctrl+M) the `ImageScaleToTotalPixels` node if you want the raw 4x output** (e.g. 1024 input -> exactly 4096 output).

### `upscale_local_to_target` in detail

Same graph but the resize node is `ImageResizeKJv2` which takes **exact width x height**. Default 3840x2160 (4K UHD). Set your target with the width/height widgets; `keep_proportion` options:
- `resize` (default) - fit inside w x h, preserve aspect ratio
- `stretch` - force exact w x h even if it distorts
- `pad` / `pad_edge` - letterbox to exact w x h with black bars (or edge-color)
- `crop` - crop to exact w x h from the center

## Local upscale model (one-time, for free upscaling)

The local upscale workflows expect an ESRGAN-family `.pth` in
`ComfyUI/models/upscale_models/`. Recommended for architectural renders:
**`4x-UltraSharp.pth`**.

Options (all ~64MB; safe on a 12GB RTX 5070 — ComfyUI auto-tiles to avoid VRAM
blow-ups):

| File | Best for |
|---|---|
| `4x-UltraSharp.pth` | Archviz — crisp edges, clean surfaces (recommended) |
| `4x_NMKD-Siax_200k.pth` | Photoreal detail retention |
| `4x_foolhardy_Remacri.pth` | Strong general-purpose |
| `RealESRGAN_x4plus.pth` | Safe baseline |

These are widely mirrored (e.g. the OpenModelDB catalog at https://openmodeldb.info).
Download the `.pth`, drop it in `ComfyUI/models/upscale_models/`, and either name
it `4x-UltraSharp.pth` or pass `--model your-file.pth` at runtime.

## 2. Usage

List everything:
```powershell
& .\standalone-env\python.exe run_fal_workflow.py --list
```

The runner **auto-starts ComfyUI** on port 8188 if it isn't running (pass
`--no-autostart` to disable). Logs go to `comfyui_autostart.log`.

### Screenshot / sketch to render

```powershell
# Flux Pro Kontext (Fal) - strong structure preservation
run_fal_workflow.py render_kontext --image cad_shot.png --prompt "photoreal dusk render, glass curtain wall, warm interior light"

# Official Google Nano Banana (uses GEMINI_API_KEY)
run_fal_workflow.py render_nanobanana_gemini --image sketch.jpg --prompt "turn this sketch into a photoreal exterior render"

# Swappable Fal edit endpoint (default openai/gpt-image-2/edit)
run_fal_workflow.py render_generic_fal --image cad_shot.png --prompt "..." --endpoint fal-ai/flux-2/edit
```

### Abstract text-to-image

```powershell
run_fal_workflow.py abstract_generic_fal --prompt "abstract parametric architecture, concrete and light" --endpoint fal-ai/flux/dev

# Swap engines: z-image, ideogram, flux-2, krea, seedream, recraft
run_fal_workflow.py abstract_generic_fal --prompt "..." --endpoint ideogram/v4
run_fal_workflow.py abstract_generic_fal --prompt "..." --endpoint fal-ai/z-image/turbo
```

### Upscale

```powershell
# FREE local GPU upscale (default)
run_fal_workflow.py upscale_local --image render.png

# Use a different local model file you downloaded
run_fal_workflow.py upscale_local --image render.png --model 4x_NMKD-Siax_200k.pth

# Opt into a PAID API upscaler when you want creative detail / max quality
run_fal_workflow.py upscale_local --image render.png --paid clarity
run_fal_workflow.py upscale_local --image render.png --paid topaz
```

### Render then upscale (render = Fal, upscale = free local)

```powershell
run_fal_workflow.py render_then_upscale --image cad_shot.png --prompt "photoreal render, golden hour"
```

## 3. Flags

| Flag | Purpose |
|---|---|
| `--prompt` | Text prompt |
| `--image` | Input image (edit/upscale workflows) |
| `--endpoint` | Swap the Fal endpoint (FalGenericAPI workflows) |
| `--model` | Swap: Fal endpoint, Gemini `model_name`, or local upscale `.pth` |
| `--extra` | Extra Fal args as a JSON string, e.g. `--extra '{"num_images":2}'` |
| `--seed` | Override seed |
| `--paid clarity\|topaz` | Use a paid API upscaler instead of local |
| `--filename-prefix` | Rename the SaveImage output prefix |
| `--host` / `--port` | ComfyUI location (default 127.0.0.1:8188) |
| `--no-autostart` | Do not launch ComfyUI automatically |
| `--timeout` | Seconds to wait for the job (default 600) |

## 4. Cost profile

| Step | Default cost |
|---|---|
| Render (Kontext / Nano Banana / generic) | Paid API |
| Abstract text-to-image | Paid API |
| **Upscale** | **Free (local GPU)** unless `--paid` |

## 5. Routing notes

- **Nano Banana edits go through the Gemini-key node** (`render_nanobanana_gemini`),
  not through Fal, per your setup. `model_name` in that workflow is swappable as
  Google ships newer Nano Banana / Nano Banana Pro image models.
- **GPT-Image-2** and **Z-Image** run through Fal via `FalGenericAPI`.
- The full swappable endpoint list per workflow is in `fal_models.json`.

## 6. Notes / troubleshooting

- These workflows are ComfyUI **API format** — you run them via the CLI, not by
  opening them in the graph editor. To edit visually, rebuild the graph in the UI.
- If a paid job runs long, the runner may time out while the job still completes;
  check `ComfyUI/output/` or the ComfyUI UI history.
- Fal image-edit nodes upload your input to Fal automatically. Do not use these
  workflows for confidential client drawings unless that is acceptable under your
  data-handling rules.
