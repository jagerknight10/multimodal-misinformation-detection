import argparse
import json

if __package__ in {None, ""}:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from soclaas import SoCLaaSClient
else:
    from .soclaas import SoCLaaSClient


def main():
    parser = argparse.ArgumentParser(description="Check SoCLaaS authentication and model access.")
    parser.add_argument("--model", help="Only display this model if present.")
    parser.add_argument("--insecure-tls", action="store_true")
    args = parser.parse_args()
    client = SoCLaaSClient(model=args.model, insecure_tls=args.insecure_tls)
    catalog = client.models()
    models = catalog.get("data", [])
    print(json.dumps({
        "model_count": len(models),
        "models": [
            {"id": m.get("id"), "display_name": m.get("soclaas", {}).get("display_name"),
             "description": m.get("soclaas", {}).get("description"),
             "capabilities": m.get("soclaas", {}).get("capabilities", [])}
            for m in models if not args.model or m.get("id") == args.model
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
