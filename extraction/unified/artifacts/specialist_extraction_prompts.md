# Specialist skill-extraction prompts

These are the full prompts for the second-stage extraction. They operate on
the structured outputs of the completed unified induction rather than sending
the raw TRUST-Instruct dataset again. Each pass must write its own skill,
provenance, memory, change log, and progress state.

## Shared extraction contract

```text
You are extracting a reusable multimodal misinformation skill from structured
observations produced from TRUST-Instruct. Use only the supplied observations,
workflows, rules, and supporting row IDs. Do not use outside knowledge,
benchmark labels as hidden hints, filenames, or copied training answers.

Merge overlapping workflows instead of listing near-duplicates. Preserve the
patterns that change the agent's decision: triggers, required inputs, ordered
steps, conditions, evidence roles, decision criteria, output fields,
uncertainty, and provenance. Distinguish a rule supported by repeated rows
from a tentative rule supported by one rare row. Exclude a pattern when it is
outside the specialist's scope or unsupported by its family.

Return strict JSON with:
{
  "skill_markdown": "complete prompt-ready skill",
  "core_patterns": [
    {
      "name": "stable pattern name",
      "purpose": "what it detects or decides",
      "trigger_conditions": ["when it applies"],
      "required_inputs": ["fields or modalities"],
      "ordered_steps": ["abstract reusable operations"],
      "conditions": ["branches and exceptions"],
      "evidence_rules": ["how evidence is used"],
      "decision_criteria": ["support/refute/uncertain criteria"],
      "output_contract": "required result fields",
      "uncertainty": "unsupported or unresolved cases",
      "supporting_row_ids": ["dataset row IDs"]
    }
  ],
  "excluded_patterns": [
    {"pattern": "...", "reason": "outside scope or unsupported"}
  ]
}

The generated skill must tell the agent what to do, what not to infer, how to
handle missing evidence, and how to report uncertainty. It must not merely
summarize the dataset.
```

## 1. Routing skill prompt

Output: `specialists/router/SKILL.md`.

```text
Create a prompt-ready routing skill for multimodal misinformation detection
using only the three supplied induced specialist skills:

1. Check_textual_factuality
2. Check_visual_manipulation
3. Check_cross_modal_consistency

The router selects one or more specialists. It does not make the final
misinformation judgement and must not invent facts.

For each specialist, extract:
- trigger conditions in the task instruction and available inputs;
- required fields to pass to that specialist;
- what the specialist can and cannot decide;
- the handoff format;
- conditions requiring multiple specialists;
- uncertainty and fallback behaviour.

Use these routing distinctions only when supported by the supplied skills:
- textual factuality: the central question is whether the caption's people,
  event, date, attribution, quantity, or context is factually supported;
- visual manipulation: the central question is whether the image itself is
  manipulated, generated, visually distorted, or a different medium;
- cross-modal consistency: the central question is whether this image depicts
  the captioned entity, event, interaction, place, or context;
- multi-route: the task combines two or more of those questions.

Return strict JSON:
{
  "skill_markdown": "complete routing skill",
  "routing_table": [
    {
      "specialist": "...",
      "trigger_conditions": ["..."],
      "required_inputs": ["..."],
      "handoff": "...",
      "not_responsible_for": ["..."]
    }
  ],
  "multi_route_conditions": ["..."],
  "fallback_route": "...",
  "uncertainty": "...",
  "supporting_specialist_patterns": ["..."]
}

SUPPLIED SPECIALIST SKILLS:
{specialist_skill_outputs}
```

## 2. Textual specialist prompt

Output: `specialists/textual/SKILL.md`.

```text
Create the specialist skill Check_textual_factuality.

Scope: determine whether the textual claim is factually supported, refuted,
misattributed, fabricated, misleading, satirical, or unresolved. The image may
be passed as context, but this specialist must not substitute visual
compatibility for textual evidence.

Input contract:
- caption or text claim;
- direct, inverse, or context evidence supplied by the task;
- optional image context only for disambiguating the textual claim;
- task instruction and requested output format.

Induce and preserve these pattern types only when supported by the textual
family observations:
- decomposition into entities, event, date, location, quantity, attribution,
  and other checkable claim elements;
- relevance filtering of sources and context;
- support versus refutation and source misattribution;
- boilerplate or generic context that is non-contributing;
- satire/parody handling, without inferring satire from a light tone alone;
- insufficient evidence and unresolved claims;
- output and uncertainty requirements.

Do not import image-manipulation rules or exact image-event visual-tie rules
unless a supplied textual observation explicitly supports them.

For every finding, distinguish:
- directly supported;
- contradicted by relevant evidence;
- irrelevant/non-contributing;
- not checked or unresolved.

Return a prompt-ready skill with a structured output containing:
claim_elements, evidence_relevance, support_or_refutation_findings,
attribution_or_source_findings, uncertainty, and Real/Fake or Insufficient
judgement as allowed by the task.

FAMILY-SPECIFIC STRUCTURED OBSERVATIONS:
{textual_rules_and_workflows}
```

## 3. Visual specialist prompt

Output: `specialists/visual/SKILL.md`.

```text
Create the specialist skill Check_visual_manipulation.

Scope: determine whether the image itself is genuine, manipulated,
AI-generated, visually distorted, or presented in a medium that changes the
claim. Keep this separate from a genuine image being paired with the wrong
caption; that latter problem belongs to cross-modal consistency.

Input contract:
- image;
- caption as context, without allowing it to dictate the image description;
- optional evidence about the image or its source;
- task instruction and requested output format.

Induce and preserve these pattern types only when supported by the visual
family observations:
- independent image description;
- visible artifacts, compositing, editing, or AI-generation cues;
- photograph versus illustration, cartoon, or other medium;
- visual attributes and identity cues;
- distinction between genuine visual content and wrong event/context pairing;
- uncertainty when image resolution or identifiers are insufficient;
- manipulation-based decision and output contract.

Do not call an image manipulated merely because it is ambiguous, unusual, or
does not match the caption. Report medium, visual observations, manipulation
evidence, and caption mismatch as separate fields.

Return a prompt-ready skill with a structured output containing:
image_description, medium, manipulation_findings, visual_identity_or_attribute
findings, evidence_used, uncertainty, and the required visual judgement.

FAMILY-SPECIFIC STRUCTURED OBSERVATIONS:
{visual_rules_and_workflows}
```

## 4. Cross-modal specialist prompt

Output: `specialists/cross_modal/SKILL.md`.

```text
Create the specialist skill Check_cross_modal_consistency.

Scope: determine whether the supplied image depicts the entity, event,
interaction, setting, date, and context asserted by the caption. The event may
be real while the image is still the wrong image for the claim.

Input contract:
- image;
- caption or text claim;
- direct evidence for checking the image;
- inverse evidence for checking the text against the image's actual context;
- optional context evidence and task instruction.

Induce and preserve these pattern types only when supported by the
cross-modal family observations:
- claim decomposition and independent image description;
- match/mismatch/inconclusive image-text comparison;
- exact entity and event-instance visual tie;
- neutral action absence versus a contradictory interaction;
- direct evidence compared with the image;
- inverse evidence compared with the text;
- empty and irrelevant evidence as non-contributing;
- partial entity mismatch weighting;
- inverse-scene or inverse-subject override;
- short captions, missing identifiers, and uncertainty;
- Real/Fake aggregation and rationale output.

Require the specialist to say whether evidence establishes the general event,
the specific image-event pairing, both, or neither. Do not use a generic
setting match as proof of an exact entity or interaction.

Return a prompt-ready skill with a structured output containing:
claim_elements, independent_image_description, image_text_consistency,
image_vs_direct_evidence, text_vs_inverse_evidence, visual_tie_result,
uncertainty, and final Real/Fake or permitted Insufficient judgement.

FAMILY-SPECIFIC STRUCTURED OBSERVATIONS:
{cross_modal_rules_and_workflows}
```

## Current implementation status

The completed unified induction has already produced the family-specific
structured observations used by these prompts. The local fallback skills in
`specialists/*/SKILL.md` were generated without new API calls because the
SOCLaAS endpoint was unavailable. The prompts above are the authoritative
specification for rerunning model consolidation when the endpoint is available.
