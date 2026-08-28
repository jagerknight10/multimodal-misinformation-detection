---
name: trust-vl-multimodal-misinformation
description: "Verify multimodal news claims by retrieving direct and inverse evidence, checking textual and visual veracity, and testing exact image-text event consistency. Use for image-caption misinformation detection and benchmark evaluation."
metadata:
  short-description: "Evidence-grounded image-text fact checking"
---

# TRUST-VL Multimodal Misinformation Detection

Use this skill when given a news image and caption and asked whether the multimodal item is real or misleading. Reproduce the observable verification workflow of TRUST-VL: retrieve evidence, reason over text and image separately, then assess their exact relationship.

## Operating rules

- Treat the caption as a set of claims to verify, not as a description of the image.
- Analyze the text and image independently before comparing them.
- Use web or search tools when available. Never imply that evidence was retrieved when it was not.
- Prefer primary sources, official records, reputable reporting, and established fact-checkers.
- Search-result snippets and generic image tags are leads, not proof.
- Absence of search results is not evidence that a claim is false.
- Do not identify a person, event, date, or location from visual resemblance alone.
- Do not call an image manipulated or AI-generated without a specific visual basis or reliable provenance evidence.
- If evidence is missing, conflicting, or inconclusive, say so explicitly and lower confidence.
- Keep the explanation concise and evidence-grounded; do not expose private chain-of-thought.

## Verification workflow

1. Parse the caption into atomic claims. Extract people, organizations, events, actions, places, dates, and implied image-event associations.
2. Inspect the image independently. Record people or possible identities, objects, actions, setting, landmarks, visible text, logos, and event/date clues. Use OCR or image inspection tools when available.
3. Retrieve direct evidence from the text. Search the exact claim first, then expand to entity-event, entity-event-date, and entity-event-location queries. Save the relevant source, URL, date, and whether it supports or contradicts each claim.
4. Retrieve inverse evidence from the image. Search distinctive image-derived entities, OCR text, logos, landmarks, captions, and event clues. Use reverse-image search when available. Do not treat a visually similar result as provenance without checking the source and event details.
5. Perform the textual check: compare every atomic claim with direct/context evidence and assess factual support, contradiction, ambiguity, satire, sentiment, or misleading framing.
6. Perform the visual check: inspect manipulation, AI-generation indicators, abnormal physical features, lighting, texture, duplicated elements, compositing, and fact-conflicting visual content. Separate visual authenticity from image-text relevance.
7. Perform the cross-modal check: compare person, event, date, location, objects, actions, scene, and provenance. Broad topical similarity is insufficient; verify the specific event association.
8. Reconcile the findings. A `Real` judgment requires the text to be supported, the image to be authentic or not materially misleading, and the image to represent the claimed event. Any supported contradiction, manipulation, or wrong-event association makes the item `Fake`.

For detailed retrieval and evidence-handling guidance, read [evidence-retrieval.md](references/evidence-retrieval.md).

## Output contract

Return these sections in order:

```text
Claim analysis:
Image analysis:
Direct evidence:
Inverse evidence:
Textual assessment:
Visual assessment:
Cross-modal assessment:
Final judgment:
```

End with exactly one of:

```text
Judgement: Real
```

or

```text
Judgement: Fake
```

When benchmark-compatible four-way classification is requested, also provide one primary class:

- `real`
- `textual_veracity_distortion`
- `visual_veracity_distortion`
- `cross-modal_consistency_distortion`

Use the class for the best-supported primary failure, while noting secondary failures separately. Preserve an internal `inconclusive` assessment when evidence is insufficient, but map it to a benchmark label only when the evaluation protocol requires it.

## Tool and benchmark behavior

- With search tools, perform both text-led direct retrieval and image-led inverse retrieval before judging.
- Without search tools, state that external verification was unavailable and distinguish model-based assessment from verified evidence.
- For MMFakeBench evaluation, keep the model, image inputs, decoding settings, tool access, and sample order fixed between baseline and skill runs. The evaluator should parse `Judgement` and the primary class separately.
- Do not use TRUST-Instruct examples as demonstrations at inference time; use the distilled procedure only.
