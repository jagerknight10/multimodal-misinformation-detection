import hashlib
import json
from pathlib import Path


CONDITIONS = ("baseline", "unified", "routed")
SPECIALIST_SKILLS = (
    "Check_textual_factuality",
    "Check_visual_manipulation",
    "Check_cross_modal_consistency",
)
ROOT = Path(__file__).parents[2]
CANONICAL_SKILL_FILES = {
    "unified": ROOT / "skills/trust-vl-multimodal-misinformation/SKILL.md",
    "evidence_adjudication": (
        ROOT / "skills/trust-vl-multimodal-misinformation/references/evidence-retrieval.md"),
    "router": ROOT / "skills/route-multimodal-misinformation/SKILL.md",
    "textual": ROOT / "skills/check-textual-factuality/SKILL.md",
    "visual": ROOT / "skills/check-visual-manipulation/SKILL.md",
    "cross_modal": ROOT / "skills/check-cross-modal-consistency/SKILL.md",
}


BASELINE_INSTRUCTIONS = """You are evaluating a multimodal misinformation benchmark.
Use the supplied news caption, image, and pre-retrieved evidence. The evidence block
contains direct text-led evidence and inverse image-led evidence. Analyze the caption
and image independently, then assess textual veracity, visual veracity, and whether
the image depicts the specific event claimed. Do not claim to have searched or cite
sources that are not present in the evidence block.

Return a brief, evidence-grounded justification. End with exactly one judgment line
and one class line in this format, using one allowed value on each line:
Judgement: Real
Class: real

Allowed classes: real, textual_veracity_distortion, visual_veracity_distortion,
cross_modal_consistency_distortion."""


def evidence_block(record):
    direct = record.get("direct_evidence", [])
    inverse = record.get("inverse_evidence", [])
    lines = [
        "PRE-RETRIEVED EVIDENCE (provided by the evaluation runner; do not perform live search):",
        "DIRECT TEXT-LED EVIDENCE:",
    ]
    lines.extend(f"{i}. {item}" for i, item in enumerate(direct, 1))
    if not direct:
        lines.append("(none supplied)")
    lines.append("INVERSE IMAGE-LED EVIDENCE:")
    lines.extend(f"{i}. {item}" for i, item in enumerate(inverse, 1))
    if not inverse:
        lines.append("(none supplied)")
    return "\n".join(lines)


def user_prompt(record):
    return f"News caption:\n{record['text']}\n\n{evidence_block(record)}"


def _read_skill(name):
    return CANONICAL_SKILL_FILES[name].read_text(encoding="utf-8")


def _benchmark_evidence_rules():
    text = _read_skill("evidence_adjudication")
    marker = "## Evidence adjudication"
    return marker + text.split(marker, 1)[1]


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skill_bundle_manifest():
    file_hashes = {
        name: _sha256(path.read_text(encoding="utf-8"))
        for name, path in CANONICAL_SKILL_FILES.items()
    }
    encoded = json.dumps(file_hashes, sort_keys=True, separators=(",", ":"))
    return {
        "bundle_hash": _sha256(encoded),
        "files": {name: str(path.relative_to(ROOT))
                  for name, path in CANONICAL_SKILL_FILES.items()},
        "file_hashes": file_hashes,
    }


def unified_skill_instructions():
    return "\n\n".join([
        _read_skill("unified"),
        "EVIDENCE ADJUDICATION RULES:\n" + _benchmark_evidence_rules(),
        """EVALUATION-MODE CONSTRAINTS:
The runner has already supplied the fixed direct and inverse evidence. Do not execute web search or reverse-image tools in this call and never imply that a search occurred.
Apply the workflow only to the supplied item. Keep unverified evidence distinct from
contradiction, use the causal primary-class rules, and finish with the required
benchmark judgment and primary class lines.""",
    ])


def skill_instructions():
    """Backward-compatible name for the unified TRUST-VL prompt."""
    return unified_skill_instructions()


def routed_skill_instructions():
    specialist_files = {
        "Check_textual_factuality": "textual",
        "Check_visual_manipulation": "visual",
        "Check_cross_modal_consistency": "cross_modal",
    }
    sections = [
        "ROUTING WORKFLOW:\n" + _read_skill("router"),
        "SHARED EVIDENCE ADJUDICATION RULES:\n" + _benchmark_evidence_rules(),
    ]
    for name in SPECIALIST_SKILLS:
        sections.append(f"SPECIALIST WORKFLOW — {name}:\n" +
                        _read_skill(specialist_files[name]))
    sections.append("""BENCHMARK EXECUTION CONSTRAINTS:
The runner has already supplied the fixed direct and inverse evidence. Do not execute
web search, reverse-image search, or any other retrieval tool, and never imply that a
search occurred unless the supplied evidence says so. Route and execute the selected
workflow(s) internally in this single response.

Follow the routed output contract and end with exactly these three lines:
Selected skills: <comma-separated exact specialist identifiers>
Judgement: <Real or Fake>
Class: <real, textual_veracity_distortion, visual_veracity_distortion, or cross_modal_consistency_distortion>""")
    return "\n\n".join(sections)


def instructions_for_condition(condition):
    condition = "unified" if condition == "skill" else condition
    if condition == "baseline":
        return BASELINE_INSTRUCTIONS
    if condition == "unified":
        return unified_skill_instructions()
    if condition == "routed":
        return routed_skill_instructions()
    raise ValueError(f"Unknown condition: {condition!r}; expected one of {CONDITIONS}")


def prompt_manifest():
    bundle = skill_bundle_manifest()
    return {
        "skill_bundle_hash": bundle["bundle_hash"],
        "skill_files": bundle["files"],
        "skill_file_hashes": bundle["file_hashes"],
        "instruction_hashes": {
            condition: _sha256(instructions_for_condition(condition))
            for condition in CONDITIONS
        },
    }
