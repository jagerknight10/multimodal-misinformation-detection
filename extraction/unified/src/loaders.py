"""Dataset and fixture loading."""

import json
from pathlib import Path
from typing import Any

from .extractor import Trajectory, to_trajectory


def load_fixture(path: Path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("fixture must contain a JSON list")
    return [item for row in rows if (item := to_trajectory(row)) is not None]


def load_representatives(path: Path):
    """Load the compact representative format emitted by sample_trajectories."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("representatives must contain a JSON list")
    return [
        Trajectory(
            str(row["row_id"]), str(row.get("image", "")),
            str(row.get("instruction", "")), str(row.get("response", "")),
            str(row["family"]),
        )
        for row in rows
    ]


def load_trust_instruct(cache_dir: Path):
    from datasets import load_dataset
    dataset = load_dataset("NUSryan/TRUST-Instruct", split="train",
                           cache_dir=str(cache_dir), streaming=False)
    return [item for row in dataset if (item := to_trajectory(row)) is not None]
