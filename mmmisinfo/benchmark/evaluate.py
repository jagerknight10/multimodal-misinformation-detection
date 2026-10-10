import argparse
import json

from .compare import _metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate one MMFakeBench prediction JSONL.")
    parser.add_argument("predictions")
    parser.add_argument("--output")
    args = parser.parse_args()
    with open(args.predictions, encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    result = {
        "rows": len(rows), "successful": sum(not row.get("error") for row in rows),
        "errors": sum(bool(row.get("error")) for row in rows),
        "binary": _metrics(rows, "predicted_binary", "ground_truth_binary"),
        "four_way": _metrics(rows, "predicted_class", "ground_truth_class"),
    }
    encoded = json.dumps(result, indent=2)
    print(encoded)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(encoded + "\n")


if __name__ == "__main__":
    main()
