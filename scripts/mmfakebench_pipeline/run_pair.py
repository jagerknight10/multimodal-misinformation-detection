import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run matched MMFakeBench baseline and TRUST-VL evaluations."
    )
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--skill-concurrency", type=int)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--skill-path")
    parser.add_argument("--insecure-tls", action="store_true")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    common = [
        "--annotations", args.annotations, "--image-root", args.image_root,
        "--max-output-tokens", str(args.max_output_tokens),
        "--temperature", str(args.temperature),
    ]
    if args.limit is not None:
        common += ["--limit", str(args.limit)]

    baseline = [sys.executable, "-m", "scripts.mmfakebench_pipeline.run", *common,
                "--condition", "baseline", "--concurrency", str(args.concurrency),
                "--output", str(output_dir / "baseline.jsonl")]
    skill = [sys.executable, "-m", "scripts.mmfakebench_pipeline.run", *common,
             "--condition", "skill", "--concurrency",
             str(args.skill_concurrency or args.concurrency),
             "--output", str(output_dir / "skill.jsonl")]
    if args.insecure_tls:
        baseline += ["--insecure-tls"]
        skill += ["--insecure-tls"]
    if args.skill_path:
        skill += ["--skill-path", args.skill_path]

    subprocess.run(baseline, check=True)
    subprocess.run(skill, check=True)


if __name__ == "__main__":
    main()
