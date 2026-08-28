import re


CLASS_NAMES = {
    "real": "real",
    "textual_veracity_distortion": "textual_veracity_distortion",
    "visual_veracity_distortion": "visual_veracity_distortion",
    "cross_modal_consistency_distortion": "cross-modal_consistency_distortion",
}


def parse_prediction(text):
    normalized = text.lower()
    judgment = None
    match = re.findall(r"judg(?:e)?ment\s*:\s*(real|fake)", normalized)
    if match:
        judgment = match[-1].title()
    elif re.search(r"finish\s*\[\s*(?:text|image)\s+refutes", normalized):
        judgment = "Fake"
    elif "mismatch" in normalized:
        judgment = "Fake"
    elif re.search(r"finish\s*\[\s*(?:original|match)", normalized):
        judgment = "Real"

    predicted_class = None
    for name, canonical in CLASS_NAMES.items():
        if name in normalized:
            predicted_class = canonical
    if predicted_class is None:
        if "text refutes" in normalized:
            predicted_class = CLASS_NAMES["textual_veracity_distortion"]
        elif "image refutes" in normalized:
            predicted_class = CLASS_NAMES["visual_veracity_distortion"]
        elif "mismatch" in normalized:
            predicted_class = CLASS_NAMES["cross_modal_consistency_distortion"]
        elif "original" in normalized or "match" in normalized:
            predicted_class = "real"
    return {"predicted_binary": judgment, "predicted_class": predicted_class}
