# AI Agent Guide: Fal + Gemini + Local Upscale ComfyUI Workflows

Reference document for AI models (Claude, GPT, Gemini, Cursor, etc.) driving this
workflow set. This file is intended to be loaded as agent context.

## 1. What this system is

A set of pre-built ComfyUI workflows that route image generation, editing, and
upscaling through:

- **Fal.ai** — text-to-image, image-to-image edit, and paid upscalers. Auth via `FAL_KEY` env var.
- **Google Gemini** (direct) — Nano Banana image editing via `GEMINI_API_KEY` env var.
- **Local GPU** — free ESRGAN upscaling via native ComfyUI nodes.

Everything runs through a local ComfyUI instance (default `http://127.0.0.1:8188`).
Only paid API calls leave the machine.

## 2. Locations

| Path | Purpose |
|---|---|
| `<comfy_root>\` | ComfyUI install root (where `main.py` lives one level down in `ComfyUI\`) — this repo's files are dropped here |
| `ComfyUI\user\default\workflows\*.json` | **UI-format** workflows (visible in ComfyUI Workflows sidebar) |
| `ComfyUI\workflows_fal\*.json` | **API-format** workflows (for POST to /prompt or the CLI runner) |
| `run_fal_workflow.py` | CLI runner (agent-driven) |
| `fal_models.json` | Workflow registry: friendly names, auth, swappable engines |
| `FAL_WORKFLOWS_README.md` | Human-facing README |
| `ComfyUI\custom_nodes\fal-api\` | Fal custom nodes (all Flux/Recraft/Seedream/Krea class types) |
| `ComfyUI\custom_nodes\comfy_nanobanana\` | Dedicated Nano Banana Gemini node (`NanoBananaGeminiImageNode`) |
| `ComfyUI\models\upscale_models\` | Local ESRGAN `.pth` files (empty until user drops one in) |
| `ComfyUI\output\` | Generated images |

## 3. Auth — read these env vars

| Env var | Used by | If unset |
|---|---|---|
| `FAL_KEY` | Any workflow with `auth: fal` in the registry | Fal nodes throw; runner preflight blocks |
| `GEMINI_API_KEY` | `render_nanobanana_gemini`, `refine_nanobanana_chain`, `refine_from_output` | Nano Banana node returns blank image |

Both are set permanently in the user's Windows env (via `setx`). New processes
inherit them; existing processes do not.

## 4. Workflow catalog

Load `fal_models.json` for the canonical registry. Summary:

### Content Engine
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `content_engine_image_studio` | FalGenericAPI x4 + LazySwitchKJ x3 | Fal | Generate by default; mode precedence is Upscale, Variations, Edit, Generate. Only the selected lazy branch executes. |

### Dedicated Nano Banana (Google Gemini)
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `nanobanana_2_generate` | NanoBananaGeminiImageNode | Gemini | Text-to-image, 2K default |
| `nanobanana_pro_generate` | NanoBananaGeminiImageNode | Gemini | Text-to-image, 4K default |

### Rendering (image edit)
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `render_kontext` | FluxProKontext_fal | Fal | Strong structure preservation |
| `render_nanobanana_gemini` | NanoBananaGeminiImageNode | Gemini | Dedicated Google node, uses GEMINI_API_KEY |
| `render_generic_fal` | FalGenericAPI (`openai/gpt-image-2/edit` default) | Fal | Swap `endpoint` widget to change model |

### Text-to-image
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `abstract_generic_fal` | FalGenericAPI (`fal-ai/z-image/turbo` default) | Fal | Swappable |
| `abstract_krea` | FalGenericAPI (`krea/v2/large/text-to-image` default) | Fal | Aesthetic-focused, Krea 2 + FLUX.1 Krea variants |
| `abstract_multigen` | FalGenericAPI (`fal-ai/flux-2` default) | Fal | Midjourney-style: one prompt -> N variations, batched into a single preview grid |
| `abstract_i2i` | FalGenericAPI (`fal-ai/flux-2/edit` default) | Fal | Image-to-image abstract restyle |

### Upscaling
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `upscale_local` | UpscaleModelLoader + ImageUpscaleWithModel + ImageScaleToTotalPixels | **FREE** | Needs `.pth`. Default 8 MP output. Mute the resize node for raw 4x. |
| `upscale_local_to_target` | UpscaleModelLoader + ImageUpscaleWithModel + ImageResizeKJv2 | **FREE** | Same as upscale_local but resize to exact WxH. Default 3840x2160. |
| `upscale_clarity` | Upscaler_fal | Fal | Adds creative detail |
| `upscale_topaz` | FalGenericAPI (`fal-ai/topaz/upscale/image`) | Fal | Highest end |
| `render_then_upscale` | FluxProKontext_fal + local | Fal (render only) | Chained; upscale is free |

### Video (image+text -> video, text -> video)
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `video_studio_fal` | FalGenericAPI + LazySwitchKJ | Fal | Text/image/first-last/reference modes |
| `video_veo3_text` | Veo3_fal | Fal (high) | 8s + native audio, best quality |
| `video_kling_image` | KlingPro16_fal | Fal | Cinematic motion, optional tail_image |
| `video_generic_fal` | FalGenericAPI | Fal | Swappable video endpoint |
| `video_preview_from_url` | LoadVideoURL | none | Preview any video URL as frames in-UI |

### 3D (image -> .glb)
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `3d_generic_fal` | FalGenericAPI | Fal | Canonical swappable single/multi-view workflow |

### Iterative refinement (Gemini-style semantic inpainting)
| Name | Engine | Cost | Notes |
|---|---|---|---|
| `refine_nanobanana_chain` | 3 x NanoBananaGeminiImageNode | Gemini | 3-stage chain, one click, mute stages to skip |
| `refine_from_output` | NanoBananaGeminiImageNode | Gemini | Uses `LoadImageOutput` ? pick prior output, refine |
| `refine_multi_engine_chain` | Kontext → FalGenericAPI → Nano Banana | Fal + Gemini | Mixed engines across 3 stages |
| `refine_from_output_generic` | FalGenericAPI | Fal | Interactive refinement via ANY Fal /edit model |

## 5. Node schema quick reference

Any agent generating or patching a workflow JSON needs the correct `class_type`
strings and input field names. Full source of truth: query
`http://127.0.0.1:8188/object_info` when ComfyUI is running. Highlights:

### `LoadImage` (built-in)
- Input: `image` (string, filename in `ComfyUI/input/`)
- Output: `IMAGE`, `MASK`

### `LoadImageOutput` (built-in)
- Input: `image` (string, filename in `ComfyUI/output/`)
- Output: `IMAGE`, `MASK`
- Purpose: iterative refinement — load a previously generated image without
  copying it into `input/`.

### `SaveImage` / `PreviewImage` (built-in)
- Inputs: `images` (IMAGE), `filename_prefix` (string, SaveImage only)
- SaveImage → permanent file in `output/`; PreviewImage → temp file, inline display in the UI.

### `UpscaleModelLoader` (built-in)
- Input: `model_name` (combo of files in `models/upscale_models/`)
- Output: `UPSCALE_MODEL`

### `ImageUpscaleWithModel` (built-in)
- Inputs: `upscale_model` (UPSCALE_MODEL), `image` (IMAGE)
- Output: `IMAGE`
- Auto-tiles on OOM; safe for large inputs on 12GB GPUs.
- **Multiplier is fixed by the `.pth`.** `4x-UltraSharp.pth` is always 4x; `2x_*.pth` is 2x. Cannot be varied from the workflow. To hit an arbitrary target size, chain a resize node after.

### `ImageScaleToTotalPixels` (built-in)
- Inputs: `image` (IMAGE), `upscale_method` (combo), `megapixels` (FLOAT), `resolution_steps` (INT)
- Output: `IMAGE`
- Use case: after an ESRGAN pass, resize to a target megapixel count. Ref: 2 MP = 1920x1080, 8 MP = ~3760x2116, 33 MP = 7680x4320 (8K UHD).

### `ImageResizeKJv2` (from `comfyui-kjnodes`)
- Required inputs (widget order): `image`, `width`, `height`, `upscale_method`, `keep_proportion`, `pad_color`, `crop_position`, `divisible_by`
- Optional: `mask`, `device`
- Outputs: `IMAGE`, `MASK`, `width` (INT), `height` (INT)
- `keep_proportion` values: `stretch`, `resize`, `pad`, `pad_edge`, `pad_edge_pixel`, `crop`, `pillarbox_blur`, `total_pixels`

### `Upscaler_fal` (Clarity — from fal-api)
- Positive prompt is **hardcoded inside the node source** (`prompt = "masterpiece, best quality, highres"`) and cannot be overridden from the workflow. Only `negative_prompt` widget is exposed.
- Resolution is controlled by `upscale_factor` (1.0-4.0). No width/height widgets. To get an exact pixel size from Clarity, chain an `ImageResizeKJv2` after.
- Tuned defaults for architectural output: `creativity=0.20`, `resemblance=0.75`, `guidance_scale=3.5`, `num_inference_steps=20`.

### `NanoBananaGeminiImageNode` (dedicated, `comfy_nanobanana` package)
- Class type: `NanoBananaGeminiImageNode`
- Required inputs: `prompt`, `model`, `batch_size`, `seed`; optional `images`, `system_prompt`, `api_key`, `aspect_ratio`, and `image_size`. Connect `images` for editing; leave it disconnected for generation.
- Current live Gemini image model IDs (as of 2026-07): `gemini-3.1-flash-image` (Nano Banana 2, recommended default), `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite, cheaper), `gemini-3-pro-image` (Nano Banana Pro, top-tier), `gemini-2.5-flash-image` (original Nano Banana). The old `-preview` suffix is 404. If a model 404s, list live IDs with `GET https://generativelanguage.googleapis.com/v1beta/models?key=<GEMINI_API_KEY>` and filter for `generateContent` support.
- Outputs: `images` (IMAGE) and `text` (STRING)
- Chainable: feed `images` into another Nano Banana node's `images` input.

### `FluxProKontext_fal` (custom, `fal-api` package)
- Inputs (order): `prompt` (STRING), `image` (IMAGE), then optional: `aspect_ratio`, `max_quality`, `guidance_scale`, `num_images`, `safety_tolerance`, `output_format`, `sync_mode`, `seed`
- Output: `IMAGE`
- Chainable.

### `FalGenericAPI` (custom, `fal-api` package)
- Inputs: `endpoint` (dropdown of Fal endpoints), `prompt` (STRING), optional `image_1` (IMAGE), `image_2` (IMAGE), `seed` (INT), `aspect_ratio` (COMBO), `extra_arguments` (STRING, JSON blob for model-specific args)
- Outputs: `image` (IMAGE), `raw_response_or_url` (STRING)
- Chainable: feed `image` output into another node's IMAGE input.
- **Swap models by changing the `endpoint` widget string.** Any string valid on Fal works, even if not in the dropdown.

### Video nodes (all from `fal-api`)

Return type `STRING` (video URL) unless noted:

- `SeedanceImageToVideo_fal` — required: `prompt`, `image`, `resolution` (`480p`/`720p`), `duration` (`5`/`10`), `camera_fixed` (bool); optional: `seed`
- `SeedanceTextToVideo_fal` — required: `prompt`, `aspect_ratio`, `resolution`, `duration`, `camera_fixed`; optional: `seed`
- `Veo3_fal` — required: `prompt`, `aspect_ratio`, `duration` (`8s`); optional: `negative_prompt`, `enhance_prompt`, `seed`, `generate_audio`
- `KlingPro16_fal` — required: `prompt`, `duration` (`5`/`10`), `aspect_ratio`; optional: `image`, `tail_image`
- `KlingMaster_fal`, `KlingPro10_fal` — similar to KlingPro16
- `WanPro_fal`, `Wan25_preview_fal` — image-to-video
- `MiniMax_fal`, `MiniMaxTextToVideo_fal` — MiniMax video
- `RunwayGen3_fal`, `LumaDreamMachine_fal`, `Veo2ImageToVideo_fal` — alternatives
- `LoadVideoURL` — ComfyUI-VideoHelperSuite-style: takes a URL, returns `frames` (IMAGE tensor), `frame_count` (INT), `video_info` (VHS_VIDEOINFO)
- `SaveStringKJ` — from `comfyui-kjnodes`: saves a STRING to a text file. Required: `string`, `filename_prefix`, `output_folder`; optional: `file_extension`. Use this to persist video/3D URLs.

### 3D via FalGenericAPI

Point `endpoint` at any of: `fal-ai/trellis-2`, `fal-ai/meshy/v6/image-to-3d`, `fal-ai/hyper3d/rodin/v2.5`, `fal-ai/pixal3d`, `fal-ai/hunyuan_world/image-to-world`. Feed `image_1` from a LoadImage. The `raw_response_or_url` STRING output slot contains the `.glb` (or scene) URL; wire it to `SaveStringKJ`. The `image` output slot is a blank tensor for these endpoints — do not use it.

### Other `_fal` nodes
`FluxDev_fal`, `FluxSchnell_fal`, `FluxPro_fal`, `FluxPro11_fal`, `FluxUltra_fal`,
`FluxLora_fal`, `FluxGeneral_fal`, `FluxPro1Fill_fal`, `FluxProKontextMulti_fal`,
`FluxProKontextTextToImage_fal`, `Ideogramv3_fal`, `Hidreamfull_fal`, `Recraft_fal`,
`Sana_fal`, `Imagen4Preview_fal`, `QwenImageEdit_fal`, `SeedEditV3_fal`,
`SeedreamV4Edit_fal`, `NanoBananaTextToImage_fal`, `NanoBananaEdit_fal`,
`ReveTextToImage_fal`, `Dreamina31TextToImage_fal`, `Upscaler_fal`,
`Seedvr_Upscaler_fal`. Source: `ComfyUI/custom_nodes/fal-api/nodes/image_node.py`
and `upscaler_node.py`.

## 5b. Resolution and batching (extra_arguments recipes)

`FalGenericAPI` only exposes `aspect_ratio` as a widget. Everything else (explicit resolution, batch count, model-specific args) goes through the `extra_arguments` JSON blob, which is merged into the Fal API call.

### Per-model max output resolution (verified against Fal API docs)
- Flux 2 family (`fal-ai/flux-2`, `/turbo`, `/pro`, `/max`, `/klein/9b`): 512-2048px per side
- Seedream v4 / v4.5 (`bytedance/seedream/v4/*`, `v4.5/*`): **up to 4096px (native 4K)** for both text-to-image and edit
- Flux Schnell / Dev: up to ~1536px
- Flux Pro v1.1 Ultra: up to ~2K
- Nano Banana / Gemini: ~1024px (aspect-ratio controlled)
- Ideogram v3/v4: up to 2048px
- Recraft v4 pro: up to 2048px
- Krea 2 family, FLUX.1 Krea: ~1MP class

### Recipes
```json
// Explicit 2K widescreen (Flux 2, Recraft, Ideogram)
{"image_size": {"width": 2048, "height": 1152}}

// Seedream 4K (only Seedream supports this natively)
{"image_size": {"width": 3840, "height": 2160}}

// Preset enum (Flux/Krea/Recraft accept these)
{"image_size": "landscape_16_9"}

// Batch (Midjourney-style N variations)
{"num_images": 4}

// Combined batch + resolution
{"num_images": 4, "image_size": {"width": 2048, "height": 1152}}

// Model-specific extras (example: Flux 2 guidance)
{"num_images": 4, "guidance_scale": 2.5, "num_inference_steps": 28}
```

### Recommended pipeline for high-res deliverables
1. Generate at model's native max via `extra_arguments`.
2. Feed to `upscale_local` (free ESRGAN, auto-tiles) for 2-4x upscale.
3. Result: 4K-8K output at only the initial API cost.

The typed `_fal` nodes (`FluxDev_fal`, `SeedreamV4Edit_fal`, `Recraft_fal`, etc.) have width/height/image_size widgets directly, so no `extra_arguments` is needed with them.

### Batching behavior
`FalGenericAPI.call_api` -> `ResultProcessor.process_image_result` (in `fal_utils.py`) stacks all `result["images"]` into a single batch tensor `[N, H, W, C]`. `SaveImage` and `PreviewImage` iterate the batch natively, so a `num_images: N` call produces N saved files and an N-image grid preview.

## 6. Two workflow formats

**UI format** (in `user/default/workflows/`) — for the ComfyUI graph editor:
```json
{
  "id": "...",
  "last_node_id": N,
  "last_link_id": M,
  "nodes": [ { "id": 1, "type": "LoadImage", "pos": [x, y], "size": [w, h], "inputs": [], "outputs": [...], "widgets_values": [...] }, ... ],
  "links": [ [link_id, from_node, from_slot, to_node, to_slot, "TYPE"], ... ],
  "groups": [],
  "config": {},
  "extra": {},
  "version": 0.4
}
```
`widgets_values` order must match the node's `INPUT_TYPES` order, excluding
connected (linked) inputs. IMAGE inputs from `LoadImage` etc. are typically
connected, so they do NOT appear in `widgets_values`.

**API format** (in `workflows_fal/`) — for POST to `/prompt`:
```json
{
  "1": { "class_type": "LoadImage", "inputs": { "image": "file.png" } },
  "2": { "class_type": "FluxProKontext_fal", "inputs": { "prompt": "...", "image": ["1", 0], ... } },
  "3": { "class_type": "SaveImage", "inputs": { "filename_prefix": "out", "images": ["2", 0] } }
}
```
Link syntax: `["<node_id>", <output_slot_index>]`. `PARAM_IMAGE`, `PARAM_PROMPT`,
etc. are placeholders the CLI runner substitutes.

## 7. CLI runner interface

```
python run_fal_workflow.py <workflow_name> [flags]
```
Flags: `--prompt`, `--image`, `--endpoint`, `--model`, `--extra` (JSON), `--seed`,
`--paid clarity|topaz`, `--filename-prefix`, `--host`, `--port`, `--no-autostart`,
`--timeout`.

Use `--list` to see all workflows with their auth cost.

The runner:
1. Loads registry, validates auth env var is present.
2. Stages input images from `--image` into `ComfyUI/input/`.
3. Substitutes `PARAM_*` placeholders.
4. Auto-starts ComfyUI (via `ComfyUI/.venv/Scripts/python.exe main.py`) if the port is down.
5. POSTs to `/prompt`, polls `/history/<prompt_id>`, prints the output filenames.

## 8. Iterative refinement (semantic inpainting) — how to drive it

Gemini/AI Studio's conversational refinement = feed previous output into a new
edit call with a targeted prompt. This system supports it four ways:

**A. In the UI, one-click multi-stage** — `refine_nanobanana_chain` or `refine_multi_engine_chain`.
Fill in each stage's prompt. Click Run. See each stage in its Preview.

**B. In the UI, interactive loop** — `refine_from_output` or `refine_from_output_generic`.
1. Run any initial workflow → image lands in `output/`.
2. Open the refine workflow. Set the `LoadImageOutput` dropdown to that image.
3. Type a targeted refinement prompt.
4. Run. New output appears in Preview and in `output/`.
5. Update the dropdown to the NEW filename. Change prompt. Run again. Repeat.

**C. Programmatic via CLI** — chain calls, feeding each output into the next:
```powershell
python run_fal_workflow.py render_kontext --image sketch.png --prompt "photoreal render" --filename-prefix stage1
# Then use output as input for the next call:
python run_fal_workflow.py render_generic_fal --image stage1_00001_.png --prompt "make sky overcast" --endpoint fal-ai/flux-2/edit
```
The runner stages any `--image` path (including from `output/`) into `input/`.

**D. Any model** — the chain works with any edit-capable model. Confirmed
chainable class types: `NanoBananaGeminiImageNode`, `FluxProKontext_fal`,
`FluxProKontextMulti_fal`, `FluxPro1Fill_fal`, `QwenImageEdit_fal`,
`SeedEditV3_fal`, `SeedreamV4Edit_fal`, `NanoBananaEdit_fal`, and `FalGenericAPI`
with any `/edit` endpoint.

## 9. Prompt patterns for semantic inpainting

- **Anchor unchanged elements**: `"keep the composition, only change the sky to sunset"`
- **Scope the edit region**: `"in the foreground trees, add autumn leaf color"`
- **Preserve identity**: `"same building, same angle, add subtle atmospheric haze"`
- **Avoid full re-descriptions** — those cause drift.

Nano Banana and Flux Kontext are strongest at preserving unmasked regions when
prompts are scoped. GPT-Image-2 and Seedream tend to reinterpret more.

## 10. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `FAL_KEY not set` | env var missing in ComfyUI process | Restart ComfyUI in a shell that has the env var, or set with `setx` and restart |
| Nano Banana returns blank image | `GEMINI_API_KEY` missing / invalid | Verify env var; the node silently returns blank on auth failure |
| `Local upscale model not found` | No `.pth` in `models/upscale_models/` | Download one (see README §1) or use `--paid clarity` |
| Workflow queues but never completes | Fal endpoint mistyped or model deprecated | Check Fal live catalog; runner has `--timeout` |
| Refinement drifts from original | Prompt too broad | Scope the prompt; anchor with "keep everything else the same" |
| UI dropdown missing new endpoints | `FAL_ENDPOINTS` list not reloaded | Restart ComfyUI (custom nodes load at startup); or type the endpoint string directly |

## 11. Adding new workflows

Preferred: create both UI-format (`user/default/workflows/`) and API-format
(`workflows_fal/`) versions, add an entry to `fal_models.json`, validate JSON
parses, then when ComfyUI is running validate `class_type` values against
`/object_info`.

Minimum viable workflow structure (API format):
```json
{
  "1": { "class_type": "LoadImage",     "inputs": { "image": "PARAM_IMAGE" } },
  "2": { "class_type": "<engine node>", "inputs": { "prompt": "PARAM_PROMPT", "image": ["1", 0], ...defaults } },
  "3": { "class_type": "SaveImage",     "inputs": { "filename_prefix": "myworkflow", "images": ["2", 0] } }
}
```

## 12. Reading the live Fal catalog

Use `python tools/update_fal_catalog.py` to query the official
`GET https://api.fal.ai/v1/models` endpoint, validate and snapshot active
models, and regenerate capability-scoped dropdowns. Pass `--deploy-node-root`
and `--deploy-workflows-dir` to update ComfyUI Desktop. Use Fal's
`metadata.category` and the matching typed node. The legacy `FalGenericAPI`
remains available only for old graphs and exceptional manual experiments.

## 13. Do NOT

- Do NOT upload confidential GRW project drawings to Fal without user consent (Fal
  workflows upload input images to Fal's storage).
- Do NOT write secrets to any file. Read them from `FAL_KEY` / `GEMINI_API_KEY` env vars only.
- Do NOT hardcode absolute Windows paths in new workflows — use `PARAM_*`
  placeholders and let the runner stage files.
- Do NOT modify `standalone-env/` — it's a bare launcher Python without torch.
  The real runtime is `ComfyUI/.venv/`.
