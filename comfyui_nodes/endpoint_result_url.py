"""Extract the primary downloadable asset URL from heterogeneous Fal results."""


def extract_asset_url(result):
    for key in ("model_glb", "model_mesh", "world_file", "file", "video", "image"):
        value = result.get(key)
        if isinstance(value, dict) and value.get("url"):
            return value["url"]
    model_urls = result.get("model_urls")
    if isinstance(model_urls, dict):
        for key in ("glb", "fbx", "obj", "usdz"):
            value = model_urls.get(key)
            if isinstance(value, dict) and value.get("url"):
                return value["url"]
    return None
