#!/usr/bin/env python
"""
run_fal_workflow.py

Agent/CLI-driven runner for the Fal + Gemini + local-upscale ComfyUI workflows
in ComfyUI/workflows_fal/.

Design goals:
  - Fire a workflow from the command line (an AI agent can drive it too).
  - Swap the model/engine per run where the workflow supports it.
  - Free local GPU upscaling by default; paid API upscalers only on request.
  - Auto-start ComfyUI if it is not already running on the target port.
  - Never write secrets to disk; keys are read from the environment.

Auth (environment variables):
  FAL_KEY         - required for any workflow whose auth == "fal"
  GEMINI_API_KEY  - required for render_nanobanana_gemini (auth == "gemini")
  (local upscale needs no key)

Examples:
  python run_fal_workflow.py --list
  python run_fal_workflow.py render_kontext --image shot.png --prompt "photoreal dusk render, glass facade"
  python run_fal_workflow.py render_generic_fal --image sketch.jpg --prompt "..." --endpoint fal-ai/flux-2/edit
  python run_fal_workflow.py abstract_generic_fal --prompt "..." --endpoint ideogram/v4
  python run_fal_workflow.py upscale_local --image render.png
  python run_fal_workflow.py upscale_local --image render.png --paid clarity
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved relative to this file so the script is location-independent)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent

# COMFY_DIR is the ComfyUI install root (the folder that contains main.py).
# Two supported layouts:
#   1. Script lives at <comfy_root>/run_fal_workflow.py, with ComfyUI/ next to it.
#      (the legacy layout on the author's machine)
#   2. Script lives inside this repo. Set COMFY_ROOT env var to your ComfyUI folder,
#      e.g. $env:COMFY_ROOT = "C:\path\to\ComfyUI".
_env_root = os.environ.get("COMFY_ROOT")
if _env_root:
    COMFY_DIR = Path(_env_root).resolve()
else:
    COMFY_DIR = SCRIPT_DIR / "ComfyUI"

# Workflows live in the repo (workflows_api/) — API-format JSONs the runner injects into.
WORKFLOWS_DIR = SCRIPT_DIR / "workflows_api"
if not WORKFLOWS_DIR.exists():
    # Legacy: workflows sat inside ComfyUI/workflows_fal on the author's machine.
    WORKFLOWS_DIR = COMFY_DIR / "workflows_fal"

INPUT_DIR = COMFY_DIR / "input"
OUTPUT_DIR = COMFY_DIR / "output"
UPSCALE_MODELS_DIR = COMFY_DIR / "models" / "upscale_models"
REGISTRY_PATH = SCRIPT_DIR / "fal_models.json"
CATALOG_PATH = SCRIPT_DIR / "catalog" / "fal_endpoint_catalog.json"
MAIN_PY = COMFY_DIR / "main.py"

FAL_NODE_CATEGORIES = {
    "FalTextToImageAPI": ("text-to-image",),
    "FalImageToImageAPI": ("image-to-image",),
    "FalImageUpscaleAPI": ("image-to-image",),
    "FalTextToVideoAPI": ("text-to-video",),
    "FalImageToVideoAPI": ("image-to-video",),
    "FalVideoToVideoAPI": ("video-to-video",),
    "FalAudioToVideoAPI": ("audio-to-video",),
    "FalTextTo3DAPI": ("text-to-3d",),
    "FalImageTo3DAPI": ("image-to-3d",),
    "Fal3DTo3DAPI": ("3d-to-3d",),
}


def _find_python():
    """Locate a Python that can actually run ComfyUI (torch installed).

    The Comfy Desktop install keeps the real runtime in ComfyUI/.venv; the
    top-level standalone-env is a bare launcher python without torch.
    """
    candidates = [
        COMFY_DIR / ".venv" / "Scripts" / "python.exe",   # Windows venv
        COMFY_DIR / ".venv" / "bin" / "python",           # posix venv
        SCRIPT_DIR / "standalone-env" / "python.exe",     # fallback
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path(sys.executable)


PYTHON_EXE = _find_python()

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8188

# Paid-upscale opt-in: maps --paid choice to the workflow that replaces a local upscale.
PAID_UPSCALE_WORKFLOWS = {
    "clarity": "upscale_clarity",
    "topaz": "upscale_topaz",
}


def log(msg):
    print(f"[run_fal] {msg}", flush=True)


def err(msg):
    print(f"[run_fal] ERROR: {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
def load_registry():
    if not REGISTRY_PATH.exists():
        err(f"Registry not found: {REGISTRY_PATH}")
        sys.exit(2)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_endpoint_catalog():
    if not CATALOG_PATH.exists():
        err(f"Endpoint catalog not found: {CATALOG_PATH}")
        err("Run: python tools/update_fal_catalog.py")
        sys.exit(2)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_fal_endpoint_node(class_type):
    return class_type == "FalGenericAPI" or class_type in FAL_NODE_CATEGORIES


def endpoint_allowed_for_node(class_type, endpoint, catalog):
    """Return whether an endpoint belongs to the node's exact Fal capability."""
    if class_type == "FalGenericAPI":
        return True
    allowed_categories = FAL_NODE_CATEGORIES.get(class_type)
    if not allowed_categories:
        return False
    model = catalog.get("models", {}).get(endpoint)
    if not isinstance(model, dict) or model.get("category") not in allowed_categories:
        return False
    if class_type == "FalImageUpscaleAPI":
        return endpoint in catalog.get("roles", {}).get("image-upscale", [])
    return True


def validate_endpoint_override(class_type, endpoint):
    catalog = load_endpoint_catalog()
    if not endpoint_allowed_for_node(class_type, endpoint, catalog):
        categories = ", ".join(FAL_NODE_CATEGORIES.get(class_type, ("legacy/unrestricted",)))
        err(f"Endpoint '{endpoint}' is not allowed by {class_type} ({categories}).")
        err("Use the matching typed workflow, or refresh the catalog if the model is newly released.")
        sys.exit(6)


def print_list(registry):
    wf = registry.get("workflows", {})
    print("\nAvailable workflows:\n")
    for name, meta in wf.items():
        auth = meta.get("auth", "?")
        cost = {"local": "FREE", "fal": "paid (FAL_KEY)", "gemini": "paid (GEMINI_API_KEY)"}.get(auth, auth)
        print(f"  {name}")
        print(f"      {meta.get('purpose', '')}")
        print(f"      cost: {cost}")
        if meta.get("swappable_field"):
            field = meta["swappable_field"]
            vals = meta.get("swappable_values", [])
            print(f"      swap --{'endpoint' if field == 'endpoint' else 'model'}: {', '.join(vals)}")
        if meta.get("requires_model_file"):
            print(f"      needs local model: {meta['requires_model_file']}")
        print()
    lm = registry.get("local_upscale_models", {})
    if lm:
        print("Local upscale models (place in ComfyUI/models/upscale_models/):")
        print(f"  recommended: {lm.get('recommended')}")
        for fn, desc in lm.get("options", {}).items():
            print(f"    {fn} - {desc}")
        print()


# ---------------------------------------------------------------------------
# ComfyUI process management
# ---------------------------------------------------------------------------
def port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def comfy_reachable(host, port):
    url = f"http://{host}:{port}/system_stats"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False


def start_comfyui(host, port, wait_seconds=180):
    if not PYTHON_EXE.exists():
        err(f"Cannot auto-start: python not found at {PYTHON_EXE}")
        err("Start ComfyUI manually, then re-run.")
        sys.exit(3)
    if not MAIN_PY.exists():
        err(f"Cannot auto-start: main.py not found at {MAIN_PY}")
        sys.exit(3)

    log(f"ComfyUI not reachable on {host}:{port}. Auto-starting...")
    cmd = [str(PYTHON_EXE), str(MAIN_PY), "--port", str(port)]
    if host not in ("127.0.0.1", "localhost"):
        cmd += ["--listen", host]

    # Detached so it keeps running; logs go to a file next to this script.
    logfile = SCRIPT_DIR / "comfyui_autostart.log"
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    with open(logfile, "ab") as lf:
        subprocess.Popen(
            cmd,
            cwd=str(COMFY_DIR),
            stdout=lf,
            stderr=lf,
            creationflags=creationflags,
        )
    log(f"Launched ComfyUI (logs: {logfile}). Waiting for it to become ready...")

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if comfy_reachable(host, port):
            log("ComfyUI is ready.")
            return
        time.sleep(2)
    err(f"ComfyUI did not become ready within {wait_seconds}s. Check {logfile}.")
    sys.exit(3)


def ensure_comfy(host, port, autostart):
    if comfy_reachable(host, port):
        return
    if autostart:
        start_comfyui(host, port)
    else:
        err(f"ComfyUI is not running on {host}:{port} and --no-autostart was set.")
        sys.exit(3)


# ---------------------------------------------------------------------------
# Auth preflight
# ---------------------------------------------------------------------------
def check_auth(meta):
    auth = meta.get("auth")
    if auth == "fal" and not os.environ.get("FAL_KEY"):
        err("This workflow needs Fal credits but FAL_KEY is not set in the environment.")
        err('Set it (PowerShell):  $env:FAL_KEY = "your-fal-key"')
        sys.exit(4)
    if auth == "gemini" and not os.environ.get("GEMINI_API_KEY"):
        err("This workflow needs a Gemini key but GEMINI_API_KEY is not set in the environment.")
        err('Set it (PowerShell):  $env:GEMINI_API_KEY = "your-gemini-key"')
        sys.exit(4)


def check_local_upscale_model(meta):
    req = meta.get("requires_model_file")
    if not req:
        return
    model_name = Path(req).name
    if not (UPSCALE_MODELS_DIR / model_name).exists():
        err(f"Local upscale model '{model_name}' not found in {UPSCALE_MODELS_DIR}")
        err("Download an ESRGAN-family .pth (see FAL_WORKFLOWS_README.md) and place it there,")
        err("or edit the workflow's UpscaleModelLoader 'model_name' to match a file you have.")
        sys.exit(5)


# ---------------------------------------------------------------------------
# Workflow loading / parameter injection
# ---------------------------------------------------------------------------
def load_workflow(meta):
    path = WORKFLOWS_DIR / meta["file"]
    if not path.exists():
        err(f"Workflow file missing: {path}")
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def stage_input_image(image_path):
    """Copy the user's image into ComfyUI/input/ and return the filename LoadImage expects."""
    src = Path(image_path)
    if not src.exists():
        err(f"Input image not found: {src}")
        sys.exit(6)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    dst_name = f"falrun_{uuid.uuid4().hex[:8]}_{src.name}"
    dst = INPUT_DIR / dst_name
    shutil.copy2(src, dst)
    log(f"Staged input image -> input/{dst_name}")
    return dst_name


def inject_params(wf, args, meta):
    """Patch PARAM_* placeholders and apply --prompt/--image/--endpoint/--model/--seed/--extra."""
    staged_image = None
    if meta.get("needs_image"):
        if not args.image:
            err(f"Workflow '{args.workflow}' requires --image.")
            sys.exit(6)
        staged_image = stage_input_image(args.image)

    for node_id, node in wf.items():
        inputs = node.get("inputs", {})
        cls = node.get("class_type", "")
        for key, val in list(inputs.items()):
            if val == "PARAM_IMAGE":
                inputs[key] = staged_image
            elif val == "PARAM_PROMPT":
                if args.prompt is None and not is_fal_endpoint_node(cls):
                    # Fal endpoint nodes tolerate an empty prompt (for example, upscalers).
                    err(f"Workflow '{args.workflow}' requires --prompt.")
                    sys.exit(6)
                inputs[key] = args.prompt if args.prompt is not None else ""

        # Optional overrides applied to the engine node.
        if args.seed is not None and "seed" in inputs:
            inputs["seed"] = args.seed
        if args.endpoint and is_fal_endpoint_node(cls) and "endpoint" in inputs:
            validate_endpoint_override(cls, args.endpoint)
            inputs["endpoint"] = args.endpoint
        if args.model:
            # For Fal endpoint nodes --model is an endpoint alias; Nano Banana uses model;
            # legacy Gemini nodes and local upscalers use model_name.
            if is_fal_endpoint_node(cls) and "endpoint" in inputs:
                validate_endpoint_override(cls, args.model)
                inputs["endpoint"] = args.model
            if "model_name" in inputs:
                inputs["model_name"] = args.model
            if cls == "NanoBananaGeminiImageNode" and "model" in inputs:
                inputs["model"] = args.model
        if args.extra and is_fal_endpoint_node(cls) and "extra_arguments" in inputs:
            # Validate it is JSON before sending.
            try:
                json.loads(args.extra)
            except json.JSONDecodeError as e:
                err(f"--extra is not valid JSON: {e}")
                sys.exit(6)
            inputs["extra_arguments"] = args.extra
        if args.filename_prefix and cls == "SaveImage" and "filename_prefix" in inputs:
            inputs["filename_prefix"] = args.filename_prefix

    return wf


# ---------------------------------------------------------------------------
# ComfyUI API: queue + poll + collect outputs
# ---------------------------------------------------------------------------
def http_post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_get_json(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def queue_prompt(host, port, wf):
    url = f"http://{host}:{port}/prompt"
    client_id = uuid.uuid4().hex
    resp = http_post_json(url, {"prompt": wf, "client_id": client_id})
    pid = resp.get("prompt_id")
    if not pid:
        err(f"No prompt_id returned. Response: {resp}")
        sys.exit(7)
    return pid


def poll_history(host, port, prompt_id, timeout_seconds):
    url = f"http://{host}:{port}/history/{prompt_id}"
    deadline = time.time() + timeout_seconds
    last_note = 0
    while time.time() < deadline:
        try:
            hist = http_get_json(url)
        except (urllib.error.URLError, OSError):
            time.sleep(1.5)
            continue
        if prompt_id in hist:
            entry = hist[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error" or status.get("completed") is False:
                err("Workflow reported an execution error:")
                err(json.dumps(status, indent=2))
                sys.exit(8)
            if "outputs" in entry and entry["outputs"]:
                return entry
        # heartbeat every ~15s
        if time.time() - last_note > 15:
            log("...still processing")
            last_note = time.time()
        time.sleep(1.5)
    err(f"Timed out after {timeout_seconds}s waiting for prompt {prompt_id}.")
    err("Long API jobs may still finish; check the ComfyUI output/ folder or UI history.")
    sys.exit(8)


def collect_outputs(entry):
    files = []
    for node_output in entry.get("outputs", {}).values():
        for img in node_output.get("images", []):
            files.append(img)
    return files


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_parser(registry):
    p = argparse.ArgumentParser(
        description="Run Fal / Gemini / local-upscale ComfyUI workflows from the CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("workflow", nargs="?", help="Workflow name (see --list).")
    p.add_argument("--list", action="store_true", help="List available workflows and exit.")
    p.add_argument("--prompt", type=str, default=None, help="Text prompt.")
    p.add_argument("--image", type=str, default=None, help="Input image path (for edit/upscale workflows).")
    p.add_argument("--endpoint", type=str, default=None, help="Swap the Fal endpoint within the workflow's capability.")
    p.add_argument("--model", type=str, default=None,
                   help="Swap the model: Fal endpoint, Gemini model_name, or local upscale .pth filename.")
    p.add_argument("--extra", type=str, default=None, help="Extra Fal endpoint args as a JSON string.")
    p.add_argument("--seed", type=int, default=None, help="Override seed on the engine node.")
    p.add_argument("--paid", choices=list(PAID_UPSCALE_WORKFLOWS.keys()), default=None,
                   help="For upscale_local/render_then_upscale: use a paid API upscaler instead of local.")
    p.add_argument("--filename-prefix", dest="filename_prefix", type=str, default=None,
                   help="Override the SaveImage filename prefix.")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--no-autostart", dest="autostart", action="store_false",
                   help="Do not auto-start ComfyUI if it is not running.")
    p.add_argument("--timeout", type=int, default=600, help="Seconds to wait for the job (default 600).")
    p.set_defaults(autostart=True)
    return p


def main():
    registry = load_registry()
    parser = build_parser(registry)
    args = parser.parse_args()

    if args.list or not args.workflow:
        print_list(registry)
        return

    workflows = registry.get("workflows", {})

    # Paid-upscale opt-in: redirect a local upscale to a paid workflow.
    if args.paid and args.workflow == "upscale_local":
        args.workflow = PAID_UPSCALE_WORKFLOWS[args.paid]
        log(f"--paid {args.paid}: using workflow '{args.workflow}' instead of local upscale.")

    if args.workflow not in workflows:
        err(f"Unknown workflow '{args.workflow}'. Use --list to see options.")
        sys.exit(2)

    meta = workflows[args.workflow]

    check_auth(meta)
    check_local_upscale_model(meta)

    wf = load_workflow(meta)
    wf = inject_params(wf, args, meta)

    ensure_comfy(args.host, args.port, args.autostart)

    log(f"Submitting workflow '{args.workflow}'...")
    prompt_id = queue_prompt(args.host, args.port, wf)
    log(f"Queued (prompt_id={prompt_id}). Polling for completion...")

    entry = poll_history(args.host, args.port, prompt_id, args.timeout)
    outputs = collect_outputs(entry)

    if not outputs:
        err("Workflow finished but produced no image outputs.")
        sys.exit(9)

    log("Done. Output file(s) in ComfyUI/output/:")
    for img in outputs:
        sub = img.get("subfolder", "")
        name = img.get("filename", "")
        rel = f"{sub}/{name}" if sub else name
        full = OUTPUT_DIR / sub / name if sub else OUTPUT_DIR / name
        view = f"http://{args.host}:{args.port}/view?filename={name}&subfolder={sub}&type=output"
        print(f"    {rel}")
        print(f"      path: {full}")
        print(f"      view: {view}")


if __name__ == "__main__":
    main()
