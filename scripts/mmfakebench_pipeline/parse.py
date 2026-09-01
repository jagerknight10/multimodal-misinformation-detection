import re


CLASS_NAMES = {
    "real": "real", "original": "real",
    "textual_veracity_distortion": "textual_veracity_distortion",
    "visual_veracity_distortion": "visual_veracity_distortion",
    "mismatch": "cross_modal_consistency_distortion",
    "cross_modal_consistency_distortion": "cross_modal_consistency_distortion",
}


def parse_prediction(text):
    """Parse explicit output lines, with conservative support for old formats."""
    normalized = text.lower()
    judgment = None
    for line in normalized.splitlines():
        match = re.match(r"^\s*judg(?:e)?ment\s*:\s*(real|fake)\s*[.!]?\s*$", line)
        if match:
            judgment = match.group(1).title()
    predicted_class = None
    for line in normalized.splitlines():
        match = re.match(r"^\s*(?:primary\s+)?class\s*:\s*([^.!]+?)\s*[.!]?\s*$", line)
        if not match:
            continue
        value = match.group(1).strip().replace(" ", "_")
        if value in CLASS_NAMES:
            predicted_class = CLASS_NAMES[value]
    if judgment is None:
        if re.search(r"finish\s*\[\s*(?:text|image)\s+refutes", normalized):
            judgment = "Fake"
        elif re.search(r"finish\s*\[\s*(?:original|match)", normalized):
            judgment = "Real"
    if judgment is None and predicted_class in {
        "textual_veracity_distortion", "visual_veracity_distortion",
        "cross_modal_consistency_distortion",
    }:
        judgment = "Fake"
    if judgment is None and predicted_class == "real":
        judgment = "Real"
    return {"predicted_binary": judgment, "predicted_class": predicted_class}
