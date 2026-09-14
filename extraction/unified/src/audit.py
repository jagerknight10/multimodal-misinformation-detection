"""Deterministic TRUST-Instruct inventory and count audit."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .extractor import FAMILIES, conversation_text, family_for, to_trajectory


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def normalize_text(text: str) -> str:
    """Conservative normalization for reproducible template counting."""
    value = text.lower()
    value = re.sub(r"https?://\S+|www\.\S+", "{url}", value)
    value = re.sub(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b", "{date}", value)
    value = re.sub(r"\b(?:19|20)\d{2}\b", "{year}", value)
    value = re.sub(r"\b\d+\b", "{number}", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def audit_rows(rows: Iterable[dict[str, Any]], write_row_ids: Path | None = None) -> dict[str, Any]:
    rows = list(rows)
    schema = {}
    columns = sorted({key for row in rows for key in row})
    for key in columns:
        values = [row.get(key) for row in rows]
        schema[key] = {
            "types": dict(Counter(_json_type(value) for value in values)),
            "null_count": sum(value is None for value in values),
            "null_rate": round(sum(value is None for value in values) / len(rows), 6) if rows else 0,
            "representative_values": [str(value)[:240] for value in values[:3]],
        }

    family_counts = Counter(family_for(row) for row in rows)
    conversation_lengths = Counter(len(row.get("conversations", [])) for row in rows)
    role_sequences = Counter(
        "->".join(str(message.get("from", "")) for message in row.get("conversations", []))
        for row in rows
    )
    reasoning = [row for row in rows if conversation_text(row, "human") and conversation_text(row, "gpt")]
    misinformation = [row for row in rows if family_for(row) in FAMILIES and to_trajectory(row)]
    exclusions = Counter()
    for row in rows:
        if family_for(row) not in FAMILIES or to_trajectory(row):
            continue
        if not str(row.get("id", "")).strip():
            exclusions["missing_id"] += 1
        if not conversation_text(row, "human"):
            exclusions["missing_human_instruction"] += 1
        if not conversation_text(row, "gpt"):
            exclusions["missing_assistant_response"] += 1
    prompt_templates = Counter(normalize_text(conversation_text(row, "human")) for row in misinformation)
    response_templates = Counter(normalize_text(conversation_text(row, "gpt")) for row in misinformation)

    if write_row_ids:
        write_row_ids.parent.mkdir(parents=True, exist_ok=True)
        with write_row_ids.open("w", encoding="utf-8") as stream:
            for index, row in enumerate(rows):
                stream.write(json.dumps({
                    "index": index, "row_id": row.get("id"),
                    "family": family_for(row),
                    "eligible": bool(to_trajectory(row)),
                }, ensure_ascii=False) + "\n")

    return {
        "raw_rows": len(rows),
        "reasoning_examples": len(reasoning),
        "misinformation_reasoning_examples": len(misinformation),
        "ineligible_target_family_rows": sum(exclusions.values()),
        "ineligibility_reasons": dict(exclusions),
        "normalized_reasoning_templates": len(response_templates),
        "distinct_task_prompts": len(prompt_templates),
        "family_counts": dict(family_counts),
        "conversation_lengths": dict(conversation_lengths),
        "role_sequences": dict(role_sequences),
        "schema": schema,
        "normalization_rule": "lowercase; replace URLs, dates, years, and digit sequences; collapse whitespace",
    }
