#!/usr/bin/env python3
"""Build family-specific skills from completed cached induction artifacts."""

import argparse
import json
from pathlib import Path


FAMILIES = {
    "textual": ("Check_textual_factuality", "textual factuality and context support/refutation"),
    "visual": ("Check_visual_manipulation", "visual veracity, medium, and manipulation"),
    "cross_modal": ("Check_cross_modal_consistency", "image-text and bidirectional evidence consistency"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--representatives", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rules = json.loads((args.source_dir / "rule_ledger.json").read_text())
    workflows = json.loads((args.source_dir / "workflow_catalog.json").read_text())
    reps = json.loads(args.representatives.read_text())
    families = {str(x["row_id"]): x["family"] for x in reps}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for family, (name, scope) in FAMILIES.items():
        ids = {row_id for row_id, value in families.items() if value == family}
        family_rules = [x for x in rules if ids.intersection(x.get("supporting_row_ids", []))
                        and not str(x.get("name", "")).startswith("rule_from_")]
        family_workflows, purposes = [], set()
        for item in sorted(workflows, key=lambda x: -len(x.get("supporting_row_ids", []))):
            if not ids.intersection(item.get("supporting_row_ids", [])):
                continue
            purpose = str(item.get("purpose", "")).strip().lower()
            if purpose in purposes:
                continue
            purposes.add(purpose)
            family_workflows.append(item)
        lines = [f"# {name}", "", f"## Scope", "", f"Assess {scope} using only the supplied task inputs and evidence.",
                 "", "## Required inputs", "", "- image (when supplied)", "- caption or text claim",
                 "- direct, inverse, or context evidence when supplied", "", "## Procedure", "",
                 "1. Extract the task-specific claim or visual facts.",
                 "2. Apply the reusable workflows below in their stated order.",
                 "3. Record support, contradiction, non-contribution, and uncertainty separately.",
                 "4. Return the required verdict with a concise evidence-linked rationale.", ""]
        lines += ["## Extracted workflows", ""]
        for item in family_workflows:
            lines += [f"### {item.get('name')}", str(item.get("purpose", "")),
                      "Steps: " + "; ".join(map(str, item.get("steps", [])))]
            if item.get("conditions"):
                lines.append("Conditions: " + "; ".join(map(str, item["conditions"])))
            if item.get("output_contract"):
                lines.append("Output: " + str(item["output_contract"]))
            lines.append("Support: " + ", ".join(item.get("supporting_row_ids", [])))
            lines.append("")
        lines += ["## Extracted decision rules", ""]
        for item in family_rules:
            lines += [f"### {item.get('name')}", str(item.get("purpose", ""))]
            for field in ("triggers", "steps", "conditions", "evidence_rules", "decision_criteria", "uncertainty"):
                if item.get(field):
                    value = "; ".join(map(str, item[field])) if isinstance(item[field], list) else str(item[field])
                    lines.append(f"{field.replace('_', ' ').title()}: {value}")
            lines.append("Support: " + ", ".join(item.get("supporting_row_ids", [])))
            lines.append("")
        family_dir = args.output_dir / family
        family_dir.mkdir(parents=True, exist_ok=True)
        (family_dir / "SKILL.md").write_text("\n".join(lines).rstrip() + "\n")
        (family_dir / "provenance.json").write_text(json.dumps({
            "family": family, "specialist": name, "representative_count": len(ids),
            "workflow_count": len(family_workflows), "rule_count": len(family_rules),
            "source": "cached unified induction; no new model calls",
        }, indent=2) + "\n")
    router = """# Route multimodal misinformation\n\n## Purpose\nRoute an input to one or more provenance-backed distortion specialists. The router selects specialists; it does not make the final judgement.\n\n## Routing rules\n\n- Route to `Check_textual_factuality` when the central question concerns whether the caption's people, event, date, attribution, quantity, or context is factually supported or refuted.\n- Route to `Check_visual_manipulation` when the central question concerns image editing, AI generation, visual artifacts, medium, or the image's own veracity.\n- Route to `Check_cross_modal_consistency` when the question concerns whether this image depicts the captioned person, event, interaction, place, or context, including direct/inverse evidence comparisons.\n- Route to multiple specialists when the task combines textual factuality, visual integrity, and image-text pairing.\n- If the task is ambiguous, route to cross-modal plus the specialist suggested by the explicit evidence fields, and preserve the uncertainty.\n\n## Handoff\nPass the original image, caption, relevant evidence fields, the selected specialist names, and the reason for each selection. Each specialist must return its own findings before final aggregation.\n"""
    router_dir = args.output_dir / "router"
    router_dir.mkdir(parents=True, exist_ok=True)
    (router_dir / "SKILL.md").write_text(router)
    (router_dir / "provenance.json").write_text(json.dumps({"source": "cached unified induction; no new model calls"}, indent=2) + "\n")
    print(json.dumps({"output_dir": str(args.output_dir), "model_calls": 0}))


if __name__ == "__main__":
    main()
