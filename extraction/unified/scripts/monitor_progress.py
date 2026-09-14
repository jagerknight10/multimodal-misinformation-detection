#!/usr/bin/env python3
"""Write a compact human-readable status snapshot for cron monitoring."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--status-file", type=Path)
    args = parser.parse_args()
    progress_path = args.run_dir / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {}
    status = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(args.run_dir),
        "completed_batch": progress.get("completed_batch", 0),
        "total_batches": progress.get("total_batches"),
        "api_calls": progress.get("api_calls", 0),
        "model": progress.get("model"),
        "last_updated_utc": progress.get("last_updated_utc"),
    }
    output = args.status_file or args.run_dir / "status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
