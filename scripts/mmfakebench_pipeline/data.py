"""Loading and canonicalising the released TRUST-VL/MMFakeBench evidence file."""

import hashlib
import json
from pathlib import Path

CLASS_MAP = {
    "original": "real", "real": "real",
    "textual_veracity_distortion": "textual_veracity_distortion",
    "visual_veracity_distortion": "visual_veracity_distortion",
    "mismatch": "cross_modal_consistency_distortion",
    "cross_modal_consistency_distortion": "cross_modal_consistency_distortion",
}


def _read_records(path):
    path = Path(path)
    with path.open(encoding="utf-8") as stream:
        first = stream.read(1)
        stream.seek(0)
        records = json.load(stream) if first == "[" else [json.loads(line) for line in stream if line.strip()]
    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON list or JSONL file: {path}")
    return records


def _evidence_items(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Evidence fields must be arrays of strings")
    return [str(item).strip() for item in value if str(item).strip()]


def evidence_hash(direct_evidence, inverse_evidence):
    payload = {"direct_evidence": direct_evidence, "inverse_evidence": inverse_evidence}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def canonicalise_record(record, index, text_cap=10, image_cap=10):
    sample_id = str(record.get("question_id") or record.get("id") or index)
    direct = _evidence_items(record.get("direct_evidence"))[:text_cap]
    inverse = _evidence_items(record.get("inverse_evidence"))[:image_cap]
    fake_cls = str(record.get("fake_cls", "")).strip().lower()
    reference = str(record.get("reference", "")).strip().lower()
    truth_binary = reference.title() if reference in {"real", "fake"} else None
    truth_class = CLASS_MAP.get(fake_cls)
    if truth_binary is None and truth_class == "real":
        truth_binary = "Real"
    if truth_binary is None and truth_class in {
        "textual_veracity_distortion", "visual_veracity_distortion",
        "cross_modal_consistency_distortion",
    }:
        truth_binary = "Fake"
    if not record.get("text") or not record.get("image_path"):
        raise ValueError(f"Record {sample_id} is missing text or image_path")
    return {
        "sample_id": sample_id, "index": index, "text": str(record["text"]),
        "image_path": str(record["image_path"]), "direct_evidence": direct,
        "inverse_evidence": inverse,
        "evidence_hash": evidence_hash(direct, inverse),
        "ground_truth_binary": truth_binary, "ground_truth_class": truth_class,
    }


def align_to_annotations(records, annotations_path, drop_unmatched=False):
    annotations = _read_records(annotations_path)
    by_text = {row.get("text"): (i, row) for i, row in enumerate(annotations)}
    aligned, unmatched = [], []
    for record in records:
        match = by_text.get(record["text"])
        if match is None:
            unmatched.append(record)
            if drop_unmatched:
                continue
            raise ValueError(f"No validation annotation matches caption for {record['sample_id']}")
        validation_index, annotation = match
        annotation_class = CLASS_MAP.get(str(annotation.get("fake_cls", "")).lower())
        if annotation_class != record.get("ground_truth_class"):
            raise ValueError(f"Label mismatch for validation index {validation_index}")
        aligned_record = dict(record)
        aligned_record.update({
            "evidence_image_path": record["image_path"],
            "image_path": str(annotation["image_path"]),
            "validation_index": validation_index,
            "validation_ground_truth_binary": annotation.get("gt_answers"),
            "validation_ground_truth_class": annotation.get("fake_cls"),
        })
        aligned.append(aligned_record)
    return aligned, unmatched


def load_evidence(path, text_cap=10, image_cap=10, annotations_path=None,
                  drop_unmatched=False):
    records = [canonicalise_record(row, i, text_cap, image_cap)
               for i, row in enumerate(_read_records(path))]
    ids = [row["sample_id"] for row in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Evidence file contains duplicate sample IDs")
    if annotations_path:
        records, _ = align_to_annotations(records, annotations_path, drop_unmatched)
    return records


def select_stratified(records, limit):
    """Deterministically select a pilot while preserving class representation."""
    if limit is None or limit >= len(records):
        return list(records)
    if limit <= 0:
        return []
    groups = {}
    for row in records:
        groups.setdefault(row.get("ground_truth_class") or "unknown", []).append(row)
    selected, positions = [], {key: 0 for key in sorted(groups)}
    while len(selected) < limit:
        progressed = False
        for key in sorted(groups):
            if positions[key] < len(groups[key]) and len(selected) < limit:
                selected.append(groups[key][positions[key]])
                positions[key] += 1
                progressed = True
        if not progressed:
            break
    return selected


def load_annotations(path):
    return _read_records(path)


def resolve_image(image_root, image_path):
    root = Path(image_root)
    relative = str(image_path).lstrip("/")
    candidates = [root / relative, root / Path(relative).name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Image not found: {image_path} (searched under {root})")
