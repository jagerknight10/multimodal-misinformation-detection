"""Deterministic grouping and representative selection for induction."""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from typing import Any

from .audit import normalize_text
from .extractor import Trajectory


OPERATION_CUES = (
    ("describe_image", r"\b(describe|depict|shows|image)\b"),
    ("decompose_claim", r"\b(analy[sz]|decompos|claim|text|caption)\b"),
    ("use_evidence", r"\b(evidence|source|support|refute|consistent)\b"),
    ("compare_modalities", r"\b(compare|cross.?modal|image.?text|match|mismatch)\b"),
    ("inspect_manipulation", r"\b(manipulat|edit|generat|artifact|visual)\b"),
    ("make_judgment", r"\b(judg|judg[e]?ment|conclu|verdict|real|fake)\b"),
)


def operation_signature(item: Trajectory) -> tuple[str, ...]:
    text = normalize_text(item.instruction + " " + item.response)
    return tuple(name for name, pattern in OPERATION_CUES if re.search(pattern, text))


def group_key(item: Trajectory) -> tuple[Any, ...]:
    evidence = tuple(tag for tag in ("direct", "inverse", "context")
                     if f"<{tag} evidence>" in item.instruction.lower())
    return (item.family, len(item.instruction) // 500, operation_signature(item), evidence)


def group_items(items: list[Trajectory]) -> dict[str, list[Trajectory]]:
    groups: dict[str, list[Trajectory]] = defaultdict(list)
    for item in items:
        key = json_key(group_key(item))
        groups[key].append(item)
    return dict(sorted(groups.items()))


def json_key(value: tuple[Any, ...]) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def select_representatives(groups: dict[str, list[Trajectory]], per_group: int = 3) -> list[Trajectory]:
    if per_group < 1:
        raise ValueError("per_group must be positive")
    selected: list[Trajectory] = []
    for key, members in groups.items():
        ranked = sorted(members, key=lambda item: hashlib.sha256(
            f"{key}\0{item.row_id}".encode()).hexdigest())
        selected.extend(ranked[:per_group])
    return selected


def grouping_report(items: list[Trajectory], per_group: int = 3) -> dict[str, Any]:
    groups = group_items(items)
    representatives = select_representatives(groups, per_group)
    return {
        "eligible_rows": len(items),
        "groups": len(groups),
        "representatives": len(representatives),
        "groups_by_family": dict(Counter(key.split('"')[1] if '"' in key else "unknown"
                                          for key in groups)),
        "group_sizes": Counter(map(len, groups.values())),
        "selection_rule": "stable SHA-256 ranking within family/length/operation/evidence groups",
    }
