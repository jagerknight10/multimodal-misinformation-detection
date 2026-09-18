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

FALLBACK_SKILL_FILES = {
    "evidence_adjudication": ROOT / "extraction/unified/artifacts/final_unified_skill.md",
    "unified": ROOT / "extraction/unified/artifacts/final_unified_skill.md",
    "router": ROOT / "extraction/unified/artifacts/specialists/router/SKILL.md",
    "textual": ROOT / "extraction/unified/artifacts/specialists/textual/SKILL.md",
    "visual": ROOT / "extraction/unified/artifacts/specialists/visual/SKILL.md",
    "cross_modal": ROOT / "extraction/unified/artifacts/specialists/cross_modal/SKILL.md",
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
    path = CANONICAL_SKILL_FILES[name]
    if not path.exists() and name in FALLBACK_SKILL_FILES:
        path = FALLBACK_SKILL_FILES[name]
    return path.read_text(encoding="utf-8")


def _skill_path(name):
    path = CANONICAL_SKILL_FILES[name]
    if not path.exists() and name in FALLBACK_SKILL_FILES:
        path = FALLBACK_SKILL_FILES[name]
    return path


def _benchmark_evidence_rules():
    path = CANONICAL_SKILL_FILES["evidence_adjudication"]
    if not path.exists():
        return """## Evidence adjudication
Use only the fixed evidence supplied by the runner. Keep direct evidence for
image checking separate from inverse evidence for text checking. Filter
irrelevant items before aggregation. Empty or unavailable evidence is
non-contributing, not a contradiction. Record support, contradiction, and
uncertainty separately."""
    text = _read_skill("evidence_adjudication")
    marker = "## Evidence adjudication"
    return marker + text.split(marker, 1)[1]


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skill_bundle_manifest():
    file_hashes = {
        name: _sha256(_skill_path(name).read_text(encoding="utf-8"))
        for name in CANONICAL_SKILL_FILES
    }
    encoded = json.dumps(file_hashes, sort_keys=True, separators=(",", ":"))
    return {
        "bundle_hash": _sha256(encoded),
        "files": {name: str(_skill_path(name).relative_to(ROOT))
                  for name in CANONICAL_SKILL_FILES},
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
benchmark judgment and primary class lines. Even if the skill's internal
assessment is inconclusive, map it to the required binary benchmark output.
Before any analysis, print two plain, unformatted lines with your selected
values. Then provide the analysis. Do not use Markdown emphasis around labels.
At the end, repeat the same two plain lines.
The final two non-empty lines must be exactly:
Judgement: Real or Fake
Class: real, textual_veracity_distortion, visual_veracity_distortion, or cross_modal_consistency_distortion""",
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
