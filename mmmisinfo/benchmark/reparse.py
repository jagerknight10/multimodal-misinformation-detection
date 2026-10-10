"""Reparse saved raw model responses without making additional API calls."""

import argparse
import json
from pathlib import Path

from .parse import parse_prediction


def reparse(input_path, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            row.update(parse_prediction(row.get("raw_response", "")))
            target.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Reparse saved benchmark outputs offline.")
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    reparse(args.input, args.output)


if __name__ == "__main__":
    main()
