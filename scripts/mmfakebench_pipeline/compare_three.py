"""Compare baseline, unified, and routed outputs without making API calls."""

import argparse
import json
from pathlib import Path

from .compare import compare_conditions, read_rows


def main():
    parser = argparse.ArgumentParser(description="Compare three matched MMFakeBench runs.")
    parser.add_argument("baseline")
    parser.add_argument("unified")
    parser.add_argument("routed")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = compare_conditions({
        "baseline": read_rows(args.baseline),
        "unified": read_rows(args.unified),
        "routed": read_rows(args.routed),
    })
    encoded = json.dumps(result, indent=2)
    print(encoded)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
