#!/usr/bin/env python3
"""Consolidate the completed unified induction into specialist skills."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from extraction.unified.src.clients import SoCLaaSTextClient  # noqa: E402
from extraction.unified.src.extractor import parse_json  # noqa: E402


SPECIALISTS = {
    "textual": "Check_textual_factuality",
    "visual": "Check_visual_manipulation",
    "cross_modal": "Check_cross_modal_consistency",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def call_json(client, prompt: str) -> dict:
    retry = prompt + "\nReturn minimal valid JSON only. Do not include reasoning outside JSON."
    for candidate in (prompt, retry):
        try:
            return parse_json(client.generate(candidate))
        except (ValueError, json.JSONDecodeError, RuntimeError):
            continue
    raise RuntimeError("specialist consolidation returned no valid JSON after retry")


def compact_family_context(family, row_families, rules, workflows):
    ids = {row_id for row_id, value in row_families.items() if value == family}
    selected_rules = []
    for item in rules:
        supports = ids.intersection(item.get("supporting_row_ids", []))
        if not supports:
            continue
        selected_rules.append({
            "name": item.get("name"), "purpose": item.get("purpose"),
            "triggers": item.get("triggers", []), "steps": item.get("steps", []),
            "conditions": item.get("conditions", []),
            "evidence_rules": item.get("evidence_rules", []),
            "decision_criteria": item.get("decision_criteria", []),
            "output_contract": item.get("output_contract"),
            "uncertainty": item.get("uncertainty"),
            "supporting_row_ids": sorted(supports),
        })
    selected_workflows = []
    seen_purposes = set()
    for item in sorted(workflows, key=lambda x: -len(x.get("supporting_row_ids", []))):
        supports = ids.intersection(item.get("supporting_row_ids", []))
        purpose = str(item.get("purpose", "")).strip().lower()
        if not supports or purpose in seen_purposes:
            continue
        seen_purposes.add(purpose)
        selected_workflows.append({
            "name": item.get("name"), "purpose": item.get("purpose"),
            "steps": item.get("steps", []), "conditions": item.get("conditions", []),
            "output_contract": item.get("output_contract"),
            "supporting_row_ids": sorted(supports),
        })
        if len(selected_workflows) >= 24:
            break
    return {
        "family": family,
        "representative_count": len(ids),
        "rules": selected_rules,
        "workflows": selected_workflows,
    }


def specialist_prompt(name, context, unified_skill):
    return f"""You are consolidating one distortion-specific skill from an already extracted TRUST-Instruct induction.

Specialist: {name}
Scope: use only the supplied family-specific structured observations. Do not add outside knowledge or invent rules. Merge overlapping workflows into a small number of reusable procedures. Preserve important recurrent patterns, conditional branches, evidence roles, uncertainty, output fields, and provenance row IDs. Explicitly distinguish what this specialist should assess from what belongs to another modality.

Return strict JSON:
{{
  "skill_markdown": "a complete prompt-ready specialist skill",
  "core_patterns": [{{"name":"...","trigger":"...","procedure":"...","decision":"...","supporting_row_ids":["..."]}}],
  "excluded_unresolved_patterns": ["..."],
  "supporting_row_count": 0
}}

Use this unified skill only as context; do not copy rules outside this specialist's scope:
{unified_skill}

Family-specific extracted records:
{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}
"""


def router_prompt(specialists):
    return f"""Create a prompt-ready routing skill for multimodal misinformation detection using only these three induced specialist skills.

Return strict JSON:
{{
  "skill_markdown": "routing instructions",
  "routing_table": [{{"specialist":"...","trigger_conditions":["..."],"required_inputs":["..."],"handoff":"..."}}],
  "multi_route_conditions": ["..."],
  "uncertainty": "..."
}}

The router must identify whether the task primarily concerns textual factuality, visual manipulation/veracity, cross-modal image-text consistency, or a combination. It must not make the final misinformation judgement itself. Use only the supplied skills.

SPECIALIST SKILLS:
{json.dumps(specialists, ensure_ascii=False, indent=2)}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path,
                        default=ROOT / "extraction/unified/artifacts/induction_qwen3_8_sampled")
    parser.add_argument("--representatives", type=Path,
                        default=ROOT / "extraction/unified/artifacts/representatives_sampled/representatives.json")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "extraction/unified/artifacts/specialists")
    parser.add_argument("--model", default="qwen3.8:27b")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rules = read_json(args.source_dir / "rule_ledger.json")
    workflows = read_json(args.source_dir / "workflow_catalog.json")
    reps = read_json(args.representatives)
    row_families = {str(item["row_id"]): item["family"] for item in reps}
    unified_skill = (ROOT / "extraction/unified/artifacts/final_unified_skill.md").read_text(encoding="utf-8")
    client = SoCLaaSTextClient(args.model, max_output_tokens=8000)
    specialist_outputs = {}
    for family, name in SPECIALISTS.items():
        family_dir = args.output_dir / family
        family_dir.mkdir(parents=True, exist_ok=True)
        context = compact_family_context(family, row_families, rules, workflows)
        prompt = specialist_prompt(name, context, unified_skill)
        fingerprint = hashlib.sha256(prompt.encode()).hexdigest()
        cache_path = family_dir / "consolidation.json"
        cached = read_json(cache_path) if cache_path.exists() else None
        if cached and cached.get("fingerprint") == fingerprint:
            result = cached["result"]
            api_call = False
        else:
            result = call_json(client, prompt)
            cache_path.write_text(json.dumps({"fingerprint": fingerprint, "result": result},
                                              ensure_ascii=False, indent=2) + "\n")
            api_call = True
        (family_dir / "SKILL.md").write_text(str(result.get("skill_markdown", "")).strip() + "\n",
                                               encoding="utf-8")
        (family_dir / "provenance.json").write_text(json.dumps({
            "family": family, "specialist": name, "representative_count": context["representative_count"],
            "supporting_row_count": result.get("supporting_row_count"),
            "core_patterns": result.get("core_patterns", []), "api_call": api_call,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        specialist_outputs[name] = result.get("skill_markdown", "")
        print(json.dumps({"specialist": name, "api_call": api_call,
                          "representatives": context["representative_count"]}), flush=True)
    router_dir = args.output_dir / "router"
    router_dir.mkdir(parents=True, exist_ok=True)
    prompt = router_prompt(specialist_outputs)
    fingerprint = hashlib.sha256(prompt.encode()).hexdigest()
    cache_path = router_dir / "consolidation.json"
    cached = read_json(cache_path) if cache_path.exists() else None
    if cached and cached.get("fingerprint") == fingerprint:
        result = cached["result"]
        api_call = False
    else:
        result = call_json(client, prompt)
        cache_path.write_text(json.dumps({"fingerprint": fingerprint, "result": result},
                                          ensure_ascii=False, indent=2) + "\n")
        api_call = True
    (router_dir / "SKILL.md").write_text(str(result.get("skill_markdown", "")).strip() + "\n",
                                          encoding="utf-8")
    (router_dir / "routing_table.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"router": True, "api_call": api_call,
                      "output_dir": str(args.output_dir)}), flush=True)


if __name__ == "__main__":
    main()
