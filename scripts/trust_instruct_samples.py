import argparse
import json
import os

from trust_instruct_utils import instruction_family, load_train


def main():
    parser = argparse.ArgumentParser(description="Display representative TRUST-Instruct records.")
    parser.add_argument(
        "--family",
        choices=["generic_image", "textual", "visual", "cross_modal", "other_dedicated"],
        default="cross_modal",
    )
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--cache-dir", default=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache"))
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    matches = []
    for row in load_train(args.cache_dir):
        if instruction_family(row) != args.family:
            continue
        matches.append(row)
        if len(matches) >= args.n:
            break

    payload = json.dumps(matches, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(payload)
        print(f"Wrote {len(matches)} {args.family} examples to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
