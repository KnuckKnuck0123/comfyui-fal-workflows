# ADR-002: Lazy-Routed Fal Video Studio and Endpoint-Aware Image Fields

## Status

Accepted

## Date

2026-08-04

## Context

The video workspace needs text-to-video, image-to-video, first/last-frame, and
reference-to-video without accidentally submitting several paid jobs. Seedance
2 exposes these as separate Fal endpoints with different image fields:

- Image-to-video uses `image_url` and optionally `end_image_url`.
- Reference-to-video uses `image_urls` and prompt references such as `@Image1`.

The installed `FalGenericAPI` node previously sent both `image_url` and
`image_urls` for every endpoint and had no mapping for `end_image_url`.

## Decision

Create `video_studio_fal` with four Fal branches and three nested
`LazySwitchKJ` nodes. All switches default to false, selecting text-to-video.
Mode precedence is Reference, First/Last Frame, Image-to-Video, then
Text-to-Video. Only the selected URL-producing branch executes.

Add a pure endpoint-aware upload mapper to the installed `fal-api` custom node.
It maps Seedance start/end images to `image_url` and `end_image_url`, reference
images to `image_urls`, and Kling 3 start/end images to `start_image_url` and
`end_image_url`.

## Alternatives Considered

### One generic image mapping for every endpoint

Rejected because Fal video schemas use different field names and may reject or
ignore an incorrectly named second image.

### Four disconnected workflow files

Rejected as the primary workspace because it duplicates setup and makes model
comparison and consistent output handling harder.

### Eager branches with manual muting

Rejected because one queue action could submit multiple paid video jobs.

## Consequences

- The workspace requires `fal-api` and `comfyui-kjnodes`.
- Image modes upload their source images to Fal.
- The `fal-api` schema adapter must be retained or reapplied after replacing the
  installed custom node.
- The default 720p, five-second request is intentionally conservative but still
  incurs Fal charges.
- ComfyUI must be restarted after changing the installed Python custom node.
