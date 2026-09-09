"""Reproducibility metadata and smoke-to-full transition checks."""

import json
from pathlib import Path

from .prompts import CONDITIONS, prompt_manifest


CONFIG_SCHEMA = "mmfakebench-fixed-skill-experiment-v1"


def build_run_config(run_type, evidence, annotations, image_root, sample_count,
                     model, temperature, max_output_tokens, rpm, concurrency):
    return {
        "schema": CONFIG_SCHEMA,
        "run_type": run_type,
        "evidence": str(Path(evidence).resolve()),
        "annotations": str(Path(annotations).resolve()),
        "image_root": str(Path(image_root).resolve()),
        "sample_count": sample_count,
        "conditions": list(CONDITIONS),
        "calls_per_sample": len(CONDITIONS),
        "planned_api_calls": sample_count * len(CONDITIONS),
        "retrieval": "fixed_pre_retrieved_evidence_no_live_search",
        "text_evidence_cap": 10,
        "image_evidence_cap": 10,
        "model": model,
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "rpm": rpm,
        "concurrency": concurrency,
        **prompt_manifest(),
    }


def write_run_config(config, output_dir):
    output_dir = Path(output_dir)
    path = output_dir / "run_config.json"
    result_files_exist = any((output_dir / f"{name}.jsonl").exists()
                             for name in CONDITIONS)
    if path.exists() and result_files_exist:
        previous = json.loads(path.read_text(encoding="utf-8"))
        guarded = (
            "schema", "run_type", "model", "temperature", "max_output_tokens",
            "conditions", "evidence", "annotations", "image_root",
            "skill_bundle_hash", "instruction_hashes",
        )
        changed = [field for field in guarded
                   if previous.get(field) != config.get(field)]
        if changed:
            raise ValueError(
                "Refusing to mix an existing run with changed settings: "
                + ", ".join(changed))
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def _latest_rows(path):
    rows = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                rows[str(row["sample_id"])] = row
    return rows


def validate_completed_smoke(smoke_config_path, expected_config):
    """Require a successful 4×3 smoke run with the exact full-run setup."""
    path = Path(smoke_config_path)
    if not path.is_file():
        raise ValueError(f"Smoke config not found: {path}")
    smoke = json.loads(path.read_text(encoding="utf-8"))
    if smoke.get("schema") != CONFIG_SCHEMA or smoke.get("run_type") != "smoke":
        raise ValueError("The supplied config is not a compatible smoke-run config")
    if smoke.get("sample_count") != 4:
        raise ValueError("The prerequisite smoke run must contain four stratified samples")
    guarded = (
        "schema", "model", "temperature", "max_output_tokens", "conditions",
        "evidence", "annotations", "image_root", "retrieval",
        "text_evidence_cap", "image_evidence_cap", "skill_bundle_hash",
        "skill_file_hashes", "instruction_hashes",
    )
    changed = [field for field in guarded
               if smoke.get(field) != expected_config.get(field)]
    if changed:
        raise ValueError(
            "Full run does not match the completed smoke setup: " + ", ".join(changed))

    by_condition = {}
    for condition in CONDITIONS:
        result_path = path.parent / f"{condition}.jsonl"
        if not result_path.is_file():
            raise ValueError(f"Missing smoke output: {result_path}")
        rows = _latest_rows(result_path)
        if len(rows) != 4:
            raise ValueError(f"Smoke condition {condition} has {len(rows)} rows; expected 4")
        expected_instruction = smoke["instruction_hashes"][condition]
        for row in rows.values():
            if row.get("error"):
                raise ValueError(f"Smoke condition {condition} contains an API error")
            if not row.get("predicted_binary") or not row.get("predicted_class"):
                raise ValueError(f"Smoke condition {condition} contains an unparsed prediction")
            if row.get("model") != smoke["model"]:
                raise ValueError(f"Smoke condition {condition} contains another model")
            if row.get("instructions_hash") != expected_instruction:
                raise ValueError(f"Smoke condition {condition} used different instructions")
            if row.get("skill_bundle_hash") != smoke["skill_bundle_hash"]:
                raise ValueError(f"Smoke condition {condition} used another skill bundle")
        by_condition[condition] = rows

    common = set.intersection(*(set(rows) for rows in by_condition.values()))
    if len(common) != 4:
        raise ValueError("Smoke conditions do not contain the same four samples")
    for sample_id in common:
        hashes = {by_condition[name][sample_id].get("evidence_hash") for name in CONDITIONS}
        if len(hashes) != 1:
            raise ValueError(f"Smoke evidence differs for sample {sample_id}")
        if not by_condition["routed"][sample_id].get("selected_skills"):
            raise ValueError(f"Routed smoke output omitted skill selection for {sample_id}")
    return {"samples": 4, "conditions": len(CONDITIONS), "calls": 12,
            "skill_bundle_hash": smoke["skill_bundle_hash"]}
