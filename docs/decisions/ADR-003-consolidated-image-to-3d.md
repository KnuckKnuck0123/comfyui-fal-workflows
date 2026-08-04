# ADR-003: Consolidate Image-to-3D Models into One Workflow

## Status

Accepted

## Date

2026-08-04

## Context

The repository had separate Trellis, Meshy, and Rodin workflows plus a generic
workflow with the same graph shape. This duplicated maintenance without adding
model-specific control. Fal's current models also support different input and
output fields: single-image models use `image_url`, multi-view models use
`image_urls`, and returned assets may be under `model_glb`, `model_mesh`, or
`world_file`.

## Decision

Keep `3d_generic_fal` as the sole image-to-3D workflow. Give it two image inputs
and a model dropdown containing Trellis 2, Meshy 6 single-image, Meshy 6
multi-image, Rodin 2.5, Pixal3D, and Hunyuan World. Route uploads and returned
asset URLs according to each endpoint's schema.

Remove the standalone Trellis, Meshy, and Rodin GUI/API workflows and their
registry entries.

## Consequences

- One workflow now covers object reconstruction, multi-view reconstruction,
  and image-to-world generation.
- Meshy Multi and Rodin can consume both connected views.
- The saved text file contains the primary downloadable asset URL.
- Hunyuan World produces a navigable world asset, not a conventional GLB object.
- Input images cross the local trust boundary and are uploaded to Fal.
