"""Run one cached Serper request and print a brief result summary."""

import argparse
import getpass
import os
from pathlib import Path

from .serper import SerperError, cached_search


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--endpoint", choices=("search", "images"), default="search")
    parser.add_argument("--cache-dir", type=Path, default=Path("data/evidence/serper_smoke"))
    args = parser.parse_args()

    try:
        result, cache_path, hit = cached_search(args.query, args.endpoint, args.cache_dir)
    except SerperError as exc:
        if "SERPER_API_KEY is required" not in str(exc):
            raise SystemExit(str(exc)) from exc
        key = os.environ.get("SERPER_API_KEY") or getpass.getpass("Serper API key: ")
        try:
            result, cache_path, hit = cached_search(args.query, args.endpoint, args.cache_dir, key)
        except SerperError as retry_exc:
            raise SystemExit(str(retry_exc)) from retry_exc

    print(f"{'CACHE HIT' if hit else 'SAVED'} {cache_path}")
    response = result["response"]
    print(f"endpoint={args.endpoint} keys={list(response)}")
    field = "images" if args.endpoint == "images" else "organic"
    for rank, item in enumerate(response.get(field, [])[:5], 1):
        print(f"{rank}. {item.get('title', '')} | {item.get('link', '')}")
        if item.get("snippet"):
            print(f"   {item['snippet'][:350]}")


if __name__ == "__main__":
    main()
