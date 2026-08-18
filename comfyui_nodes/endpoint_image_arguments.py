"""Map uploaded ComfyUI images to endpoint-specific Fal input fields.

Mappings for current endpoint families are verified against the OpenAPI schemas
returned by ``GET https://api.fal.ai/v1/models?expand=openapi-3.0``.
"""


def map_uploaded_images(endpoint, uploaded_urls):
    if not uploaded_urls:
        return {}

    if endpoint == "minimax/h3/reference-to-video":
        return {"reference_image_urls": uploaded_urls}
    if endpoint.endswith("/reference-to-video"):
        return {"image_urls": uploaded_urls}

    if endpoint in {
        "fal-ai/meshy/v6/multi-image-to-3d",
        "fal-ai/hyper3d/rodin/v2.5",
        "meshy/v7/multi-image-to-3d",
    }:
        return {"image_urls": uploaded_urls}
    if endpoint == "hitem3d/hi3d/multi-view-to-3d":
        mapped = {"front_image_url": uploaded_urls[0]}
        if len(uploaded_urls) > 1:
            mapped["right_image_url"] = uploaded_urls[1]
        return mapped
    if endpoint in {
        "fal-ai/trellis-2",
        "fal-ai/meshy/v6/image-to-3d",
        "fal-ai/pixal3d",
        "fal-ai/hunyuan_world/image-to-world",
        "meshy/v7/image-to-3d",
        "hitem3d/hi3d/image-to-3d",
    }:
        return {"image_url": uploaded_urls[0]}

    if endpoint.startswith("blackforestlabs/flux-3/first-last-frame-to-video"):
        mapped = {"start_image_url": uploaded_urls[0]}
        if len(uploaded_urls) > 1:
            mapped["end_image_url"] = uploaded_urls[1]
        return mapped
    if endpoint.startswith("blackforestlabs/flux-3/keyframes-to-video"):
        keyframes = [{"image_url": uploaded_urls[0], "frame_index": 0}]
        if len(uploaded_urls) > 1:
            keyframes.append({"image_url": uploaded_urls[1], "frame_index": 120})
        return {"keyframes": keyframes}
    if endpoint.startswith("blackforestlabs/flux-3/image-to-video"):
        return {"image_url": uploaded_urls[0]}

    first_last_families = (
        "bytedance/seedance-2.0/",
        "bytedance/seedance-2.5/",
        "lightricks/ltx-2.5/",
        "minimax/h3/image-to-video",
    )
    if endpoint.endswith("/image-to-video") or "/image-to-video/" in endpoint:
        if endpoint.startswith(first_last_families):
            mapped = {"image_url": uploaded_urls[0]}
            if len(uploaded_urls) > 1:
                mapped["end_image_url"] = uploaded_urls[1]
            return mapped
        if endpoint.startswith("fal-ai/kling-video/v3/"):
            mapped = {"start_image_url": uploaded_urls[0]}
            if len(uploaded_urls) > 1:
                mapped["end_image_url"] = uploaded_urls[1]
            return mapped

    return {"image_url": uploaded_urls[0], "image_urls": uploaded_urls}
