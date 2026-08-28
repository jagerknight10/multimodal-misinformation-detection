from pathlib import Path


BASELINE_INSTRUCTIONS = """You are evaluating a multimodal misinformation benchmark.
Given the news caption and image, directly classify the item. Decide whether it is real,
textually false, visually false/manipulated, or an image-caption mismatch.
Use the retrieved evidence supplied with the item. Do not claim a search or source
unless it appears in that retrieved evidence.
Return a brief justification, then end with exactly these two lines:
Judgement: Real or Fake
Class: real, textual_veracity_distortion, visual_veracity_distortion, or cross-modal_consistency_distortion
"""


def skill_instructions(skill_path=None):
    path = Path(skill_path or Path(__file__).parents[2] /
                "skills/trust-vl-multimodal-misinformation/SKILL.md")
    return path.read_text(encoding="utf-8") + """

Apply this workflow to the supplied benchmark item.
Runtime constraint: external web, search, and reverse-image tools are not
executed inside this image-judgment call. Never claim to have searched, retrieved,
or consulted a source unless it appears in the supplied retrieved-evidence block.
The evidence block was collected by the evaluation runner before this call.
"""
