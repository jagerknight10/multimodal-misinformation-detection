import json
from pathlib import Path


def load_annotations(path):
    with open(path, encoding="utf-8") as stream:
        records = json.load(stream)
    if not isinstance(records, list):
        raise ValueError("MMFakeBench annotation file must contain a JSON list")
    return records


def resolve_image(image_root, image_path):
    root = Path(image_root)
    relative = str(image_path).lstrip("/")
    candidates = [root / relative, root / Path(relative).name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Image not found: {image_path} (searched under {root})")
