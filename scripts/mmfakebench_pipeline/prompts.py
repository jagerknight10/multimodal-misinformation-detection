from pathlib import Path


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


def skill_instructions(skill_path=None):
    path = Path(skill_path or Path(__file__).parents[2] /
                "skills/trust-vl-multimodal-misinformation/SKILL.md")
    return path.read_text(encoding="utf-8") + """

Evaluation-mode constraint: the runner has already supplied the fixed direct and
inverse evidence. Do not execute web search or reverse-image tools in this call and
never imply that a search occurred unless the supplied evidence says so. Apply the
workflow to the supplied item and finish with the required benchmark judgment and
primary class lines."""
