# Workshop Quickstart Card

One page. Print it or keep it open in a second tab.

---

## Before you start

- [ ] ComfyUI is running (the **ComfyUI Desktop** app window is open on the canvas)
- [ ] You have a Fal.ai account with **at least $5 credit** — [fal.ai/dashboard/billing](https://fal.ai/dashboard/billing)
- [ ] You have a Fal API key — [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
- [ ] `FAL_KEY` is set in your environment and ComfyUI was restarted after
- [ ] `fal-api` custom node is installed (via ComfyUI Manager)
- [ ] Workflow JSONs from `workflows_gui/` are copied into
      `<ComfyUI>/user/default/workflows/`

---

## The 3-workflow starter track

Run these in order — 15 minutes total.

### 1. `abstract_flux` — text → image (~$0.025)

- Open `abstract_flux` from the Workflows sidebar.
- Edit the prompt on the **Flux Dev (fal)** node.
- Prompt template:
  > `[building type] in [material palette], [time of day], [light quality], architectural photography, editorial style`
- Example:
  > `concrete community library in birch and travertine, golden hour, side raking light, architectural photography, editorial style`
- Hit **Queue**. ~15 sec.

### 2. `render_kontext` — sketch → photoreal render (~$0.05)

- Open `render_kontext`.
- **Load Image**: upload a Rhino/Revit screenshot or hand sketch.
- **Flux Pro Kontext (fal)** prompt:
  > `photoreal architectural render, [material palette], [weather/time], people at street level, editorial magazine style`
- Hit **Queue**. ~30 sec.

### 3. `upscale_local` — free 4× upscale (**$0**)

- Requires `RealESRGAN_x4plus.pth` in `ComfyUI/models/upscale_models/`.
- Open `upscale_local`, upload your render from step 2.
- Hit **Queue**. Local GPU, no API traffic.

---

## Prompt patterns that work well

| Goal | Add to prompt |
|---|---|
| Photoreal | `architectural photography, editorial style, natural light` |
| Overcast documentary look | `overcast afternoon, diffused light, muted palette` |
| Golden hour hero shot | `golden hour, warm rim light, long shadows` |
| Interior render | `wide-angle interior, natural + ambient lighting, warm materials` |
| Aerial/urban | `drone photography, morning haze, urban context` |
| Materiality emphasis | `close-up material study, tactile detail, [material] surface` |

Keep prompts under ~40 words. Comma-separated phrases beat run-on sentences.

---

## If it breaks

| Symptom | Fix |
|---|---|
| `401 Unauthorized` | `FAL_KEY` not set. Restart ComfyUI from the shell where you set it. |
| `402 Insufficient credit` | Top up at fal.ai/dashboard/billing |
| `Node type 'FluxDev_fal' not found` | Install `fal-api` in ComfyUI Manager, restart |
| Nothing happens for 5+ min | Video/3D is slow. Check ComfyUI terminal window. |
| Local upscale error | Drop an ESRGAN `.pth` into `ComfyUI/models/upscale_models/`, restart |

---

## Where to go next

- Try the video track: `video_veo3_text` (best quality, includes audio)
- Try 3D: `3d_image_to_glb_trellis` — image → downloadable `.glb`
- Try refinement chains: `refine_from_output` — iterate on a prior result
- Full catalog: [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md)
- The CLI runner for batching: main [`README.md`](README.md#advanced-the-cli-runner-run_fal_workflowpy)
