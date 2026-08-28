import argparse
import json
import os
from collections import Counter

from trust_instruct_utils import (
    base_summary,
    evidence_tags,
    final_judgment,
    instruction_family,
    instruction_style,
    load_train,
    summarize_counter,
)


def main():
    parser = argparse.ArgumentParser(description="Summarize TRUST-Instruct layout and instruction types.")
    parser.add_argument("--cache-dir", default=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache"))
    parser.add_argument("--limit", type=int, default=None, help="Inspect only the first N rows.")
    args = parser.parse_args()

    summary = base_summary()
    for row in load_train(args.cache_dir):
        summary["rows"] += 1
        summary["families"][instruction_family(row)] += 1
        summary["styles"][instruction_style(row)] += 1
        summary["conversation_lengths"][len(row.get("conversations", []))] += 1
        summary["image_prefixes"][row.get("image", "").split("/")[0]] += 1
        summary["id_suffixes"][row.get("id", "").split("-", 1)[-1]] += 1
        summary["final_judgments"][final_judgment(row)] += 1
        for tag, present in evidence_tags(row).items():
            if present:
                summary["evidence_tags"][tag] += 1

        if args.limit is not None and summary["rows"] >= args.limit:
            break

    output = {
        "rows_inspected": summary["rows"],
        "families": summarize_counter(summary["families"]),
        "conversation_lengths": summarize_counter(summary["conversation_lengths"]),
        "conversation_styles": summarize_counter(summary["styles"]),
        "image_path_prefixes": summarize_counter(summary["image_prefixes"]),
        "id_suffixes": summarize_counter(summary["id_suffixes"]),
        "records_with_evidence_tags": summarize_counter(summary["evidence_tags"]),
        "final_judgments": summarize_counter(summary["final_judgments"]),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
