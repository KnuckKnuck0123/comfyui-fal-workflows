# ADR-001: Hosted-First Content Engine as ComfyUI Workspaces

## Status

Accepted

## Date

2026-08-04

## Context

The content engine should work for people without strong local GPUs. The existing
workflow repository already has tested Fal and Gemini templates, while the
installed `fal-api` package provides generic hosted inference through
`FalGenericAPI`. Reimplementing Fal transport would duplicate working code and
create another authentication surface.

A single canvas with several paid branches can accidentally queue every branch.
The installed `LazySwitchKJ` node marks its data inputs as lazy, allowing a
single selected branch to execute while the other hosted branches remain idle.

Images sent through a Fal edit or upscale branch cross the local trust boundary
and are uploaded to Fal. Internal or confidential project imagery must not be
used unless that transfer is permitted.

## Decision

Build the Content Engine as source-controlled ComfyUI workspace templates that
compose existing provider nodes.

The first vertical slice is `content_engine_image_studio` with four modes:

1. Generate.
2. Edit / Render.
3. Variations.
4. Upscale.

Three nested `LazySwitchKJ` nodes route only one branch to a shared Preview and
Save output. Mode precedence is Upscale, then Variations, then Edit, then
Generate. All toggles default to false, selecting Generate.

API keys remain environment variables. Workflow JSON must never contain keys,
tokens, or credentials. Nano Banana remains in its dedicated Google workflows
and is not duplicated in this Fal workspace.

## Alternatives Considered

### New custom Fal transport nodes

Rejected for the first slice because `fal-api` already handles uploads, queueing,
result conversion, and endpoint execution.

### Four unrelated workflow files

Rejected as the product shell because those capabilities already exist. The
engine needs a coherent workspace rather than more disconnected templates.

### All branches active with manual muting

Rejected because a user can unintentionally run several paid endpoints in one
queue operation.

## Consequences

- The first slice requires `fal-api` and `comfyui-kjnodes`.
- Users can work on low-compute machines while retaining the ComfyUI canvas.
- Selected edit and upscale modes upload their input images to Fal.
- Provider-specific controls continue to use `extra_arguments` JSON until a
  later interface layer presents schema-aware controls.
- Video, 3D, and a custom frontend launcher remain later vertical slices.
