import argparse
import json
import os
from collections import Counter

from trust_instruct_utils import final_judgment, instruction_family, load_train


def main():
    parser = argparse.ArgumentParser(description="Check TRUST-Instruct record consistency and artifacts.")
    parser.add_argument("--cache-dir", default=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    counts = Counter()
    examples = []
    inspected = 0

    for row in load_train(args.cache_dir):
        inspected += 1
        conversations = row.get("conversations", [])
        human_text = "\n".join(m.get("value", "") for m in conversations if m.get("from") == "human")
        gpt_text = "\n".join(m.get("value", "") for m in conversations if m.get("from") == "gpt")
        row_id = row.get("id", "")
        family = instruction_family(row)

        if not row.get("id"):
            counts["missing_id"] += 1
        if not row.get("image"):
            counts["missing_image"] += 1
        if not conversations:
            counts["missing_conversations"] += 1
        if any(m.get("from") not in {"human", "gpt"} for m in conversations):
            counts["unexpected_speaker"] += 1
        if family != "generic_image" and "<image>" not in human_text:
            counts["dedicated_missing_image_token"] += 1
        if family != "generic_image" and final_judgment(row) == "missing":
            counts["dedicated_missing_final_judgment"] += 1

        id_label = row_id.lower().rsplit("-", 1)[-1]
        judgment = final_judgment(row).lower()
        if id_label in {"real", "fake"} and judgment in {"real", "fake"} and id_label != judgment:
            counts["id_judgment_mismatch"] += 1
            if len(examples) < 10:
                examples.append({"id": row_id, "judgment": final_judgment(row), "family": family})

        if "no obvious signs of manipulation" in gpt_text.lower() and "image is manipulated" in gpt_text.lower():
            counts["possible_manipulation_contradiction"] += 1

        if args.limit is not None and inspected >= args.limit:
            break

    print(json.dumps({"rows_inspected": inspected, "checks": dict(counts), "examples": examples}, indent=2))


if __name__ == "__main__":
    main()
