"""Capability-scoped variants of the legacy FalGenericAPI ComfyUI node.

This module is deployed beside ``generic_node.py`` in ComfyUI-fal-API. The
legacy node remains registered for old graphs, while new graphs use these
typed selectors so a 3D endpoint cannot appear in an image workflow.
"""

from pathlib import Path

from .capability_catalog import CapabilityCatalogError, load_endpoint_choices
from .generic_node import FalGenericAPI


CATALOG_PATH = Path(__file__).with_name("fal_endpoint_catalog.json")


def _choices(*, categories=(), role=None, fallback):
    try:
        choices = load_endpoint_choices(CATALOG_PATH, categories=categories, role=role)
    except CapabilityCatalogError as exc:
        print(f"[FAL Capability Nodes] {exc}; using the built-in fallback")
        choices = []
    return choices or [fallback]


def _make_node(class_name, label, *, categories=(), role=None, fallback):
    endpoint_choices = _choices(categories=categories, role=role, fallback=fallback)

    class CapabilityNode(FalGenericAPI):
        @classmethod
        def INPUT_TYPES(cls):
            inputs = super().INPUT_TYPES()
            inputs["required"]["endpoint"] = (endpoint_choices, {"default": endpoint_choices[0]})
            return inputs

        CATEGORY = f"FAL/Capability/{label}"

    CapabilityNode.__name__ = class_name
    CapabilityNode.__qualname__ = class_name
    return CapabilityNode


FalTextToImageAPI = _make_node(
    "FalTextToImageAPI", "Image / Generate", categories=("text-to-image",), fallback="fal-ai/flux-2"
)
FalImageToImageAPI = _make_node(
    "FalImageToImageAPI", "Image / Edit", categories=("image-to-image",), fallback="fal-ai/flux-2/edit"
)
FalImageUpscaleAPI = _make_node(
    "FalImageUpscaleAPI", "Image / Upscale", role="image-upscale", fallback="fal-ai/topaz/upscale/image"
)
FalTextToVideoAPI = _make_node(
    "FalTextToVideoAPI", "Video / Text", categories=("text-to-video",),
    fallback="blackforestlabs/flux-3/text-to-video",
)
FalImageToVideoAPI = _make_node(
    "FalImageToVideoAPI", "Video / Image", categories=("image-to-video",),
    fallback="blackforestlabs/flux-3/image-to-video",
)
FalVideoToVideoAPI = _make_node(
    "FalVideoToVideoAPI", "Video / Edit", categories=("video-to-video",),
    fallback="blackforestlabs/flux-3/extend-video",
)
FalAudioToVideoAPI = _make_node(
    "FalAudioToVideoAPI", "Video / Audio", categories=("audio-to-video",),
    fallback="lightricks/ltx-2.5/audio-to-video/fast",
)
FalImageTo3DAPI = _make_node(
    "FalImageTo3DAPI", "3D / Image", categories=("image-to-3d",), fallback="meshy/v7/image-to-3d"
)
FalTextTo3DAPI = _make_node(
    "FalTextTo3DAPI", "3D / Text", categories=("text-to-3d",), fallback="fal-ai/meshy/v6/text-to-3d"
)
Fal3DTo3DAPI = _make_node(
    "Fal3DTo3DAPI", "3D / Edit", categories=("3d-to-3d",), fallback="hitem3d/hi3d/texture"
)


NODE_CLASS_MAPPINGS = {
    cls.__name__: cls
    for cls in (
        FalTextToImageAPI,
        FalImageToImageAPI,
        FalImageUpscaleAPI,
        FalTextToVideoAPI,
        FalImageToVideoAPI,
        FalVideoToVideoAPI,
        FalAudioToVideoAPI,
        FalImageTo3DAPI,
        FalTextTo3DAPI,
        Fal3DTo3DAPI,
    )
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FalTextToImageAPI": "Fal Image Generate (catalog)",
    "FalImageToImageAPI": "Fal Image Edit (catalog)",
    "FalImageUpscaleAPI": "Fal Image Upscale (catalog)",
    "FalTextToVideoAPI": "Fal Text to Video (catalog)",
    "FalImageToVideoAPI": "Fal Image to Video (catalog)",
    "FalVideoToVideoAPI": "Fal Video Edit (catalog)",
    "FalAudioToVideoAPI": "Fal Audio to Video (catalog)",
    "FalImageTo3DAPI": "Fal Image to 3D (catalog)",
    "FalTextTo3DAPI": "Fal Text to 3D (catalog)",
    "Fal3DTo3DAPI": "Fal 3D Edit (catalog)",
}
