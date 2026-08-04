# Changelog

All notable changes to this project are tracked here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/) once we cut a
release; until then, work lives under **Unreleased**.

## Convention

- **Added** — new workflows, docs, features
- **Changed** — modifications to existing workflows, behaviors, or copy
- **Deprecated** — soon-to-be-removed features (with a target date)
- **Removed** — deleted workflows or features
- **Fixed** — bug fixes to workflows, runner, or docs
- **Security** — anything key/auth/permission-related

Each entry should be short but self-explanatory to a workshop student
reading it a month later. When we ship a workshop cohort, cut a version
(e.g. `[0.1.0] - 2026-07-15 — Cohort A`) and start a new **Unreleased**.

---

## [Unreleased]

*Working on this here — cut a version tag when we hit a workshop or a
meaningful milestone.*

### Added
- `content_engine_image_studio`: hosted-first workspace combining Generate, Edit / Render, Variations, and Upscale with lazy routing so only one paid Fal branch executes per queue operation.
- ADR-001 documenting the hosted-first workspace architecture, provider trust boundary, and cost-safety routing decision.
- Four dedicated Nano Banana workflow pairs in GUI and API formats: Nano Banana 2 and Nano Banana Pro, each with generation and editing variants.
- Contract tests and a deterministic generator for the Nano Banana workflow family.

### Changed
- Migrated all Nano Banana and mixed-engine templates from the legacy `NanoBanana API??` node to `NanoBananaGeminiImageNode` from `comfy_nanobanana`.
- `README.md`, `WORKSHOP.md`: reframe "ComfyUI is running" step around the
  **ComfyUI Desktop native window**, not a `127.0.0.1:8188` browser check.
  Students installing the Desktop app never touch a browser — the app IS
  the UI. Portable/standalone build noted as fallback.
- `docs/WORKFLOWS.md`: "refresh the browser" → "refresh the Workflows
  sidebar or restart ComfyUI Desktop." Also fixed a stale
  `ComfyUI/workflows_fal/` reference (now `workflows_api/` in this repo).

### Ideas / TODO
- Capture a real hero screenshot for `docs/img/hero.png`
- Dry-run the `workflows_gui/` drag-drop path on a clean ComfyUI install
- Add per-workflow example output images to `docs/img/`
- Consider a Windows `.bat` and macOS `.sh` helper that copies
  `workflows_gui/*.json` into the ComfyUI user folder in one click
- Add a "known-good models list" section to `docs/WORKFLOWS.md` for
  each swappable Fal endpoint (which ones we've tested vs. not)

---

## [0.1.0] - 2026-07-08 — Workshop-ready scaffold

First public shape of the repo, restructured to be workshop-friendly.

### Added
- 27 workflow JSONs in **two formats**:
  - `workflows_gui/` — UI-format, copy into
    `<ComfyUI>/user/default/workflows/` for drag-and-drop in the browser
  - `workflows_api/` — API-format, consumed by the CLI runner and agents
- `run_fal_workflow.py` — CLI runner with auto-start ComfyUI, auth
  preflight, param injection, and `--paid` opt-in for API upscalers
- `fal_models.json` — workflow registry (metadata, auth, swappable engines)
- `README.md` — workshop-first: BYO Fal-key walkthrough, cost table,
  3-workflow starter track, per-category catalog, troubleshooting.
  CLI runner demoted to an "Advanced" section.
- `WORKSHOP.md` — one-page student quickstart card
- `docs/WORKFLOWS.md` — full workflow reference (formerly
  `FAL_WORKFLOWS_README.md`)
- `docs/AI_AGENT_GUIDE.md` — loadable context for AI agents driving the
  runner (formerly `AI_AGENT_GUIDE.md`)
- `docs/fal-links.txt` — Fal endpoint reference links
- `docs/img/` — placeholder folder for screenshots
- `.env.example`, `.gitignore`, MIT `LICENSE`, `requirements.txt`

### Changed
- `run_fal_workflow.py`: `WORKFLOWS_DIR` now points at the repo's
  `workflows_api/` folder; a `COMFY_ROOT` env var lets users point the
  runner at any ComfyUI install rather than requiring the legacy
  `<script_dir>/ComfyUI/` layout
- `docs/AI_AGENT_GUIDE.md`: scrubbed a hard-coded personal path in the
  Locations table so the doc is portable

### Security
- `.gitignore` blocks `.env`, `*.key`, logs, model weights, and generated
  output/ so keys and heavy binaries never make it into git

---

<!--
When cutting a release:
1. Rename the top "Unreleased" section to "[X.Y.Z] - YYYY-MM-DD — short label"
2. Add a fresh empty "Unreleased" block above it with the standard subsections
3. `git tag vX.Y.Z && git push --tags`
-->
