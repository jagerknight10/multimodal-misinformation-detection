# Evidence Retrieval and Adjudication

This reference operationalizes the direct/inverse/context evidence flow used by TRUST-VL.

## Evidence channels

- **Direct evidence** is retrieved from the caption or atomic textual claims.
- **Inverse evidence** is retrieved from image-derived clues: visual entities, OCR, logos, landmarks, distinctive scenes, and reverse-image results.
- **Context evidence** is supplied by the user, benchmark, or a trusted reference such as an official record or fact-check.

Keep the channels separate. Do not use a direct search result as proof that the attached image belongs to that event.

## Direct retrieval

Use a staged query strategy:

1. Exact caption or distinctive quoted phrase.
2. Main person/organization plus event.
3. Entity plus event plus date or location.
4. Alternative spellings, names, and wording.

For each result, capture:

```text
Source:
URL:
Publication/event date:
Relevant fact:
Supports, contradicts, or unrelated:
```

Prefer contemporaneous primary reporting and official sources. Use multiple independent sources for important claims. A source that merely repeats the caption is not independent confirmation.

## Inverse retrieval

First describe the image without relying on the caption. Extract searchable clues, then search combinations such as:

- apparent person + distinctive event or setting;
- visible text or logo;
- landmark + activity;
- distinctive scene + likely location;
- reverse-image result + original publication.

Verify candidate matches by comparing the exact person, event, date, location, crop, background, and source caption. A similar person or scene is not sufficient.

If reverse-image search is unavailable, use image captions, OCR, visual search, and targeted text searches. Mark provenance as unverified when no result establishes the original event.

## Evidence adjudication

For each claim, assess:

- **Reliability:** source quality and independence.
- **Specificity:** whether it addresses the exact claim.
- **Temporal fit:** whether dates align.
- **Spatial fit:** whether locations align.
- **Identity fit:** whether people or organizations align.
- **Modality fit:** whether the evidence verifies the text, image, or their association.

Use these statuses:

```text
Supported
Contradicted
Unverified
Conflicting
Irrelevant
```

Do not convert `Unverified` into `Contradicted`. Do not convert generic evidence into event-level verification.

### Evidence strength

Judge every relevant item on five dimensions:

- **Authority:** primary record, official source, established reporting, named fact-check, anonymous repost, or unknown source.
- **Independence:** original reporting versus copies of the same claim or source.
- **Specificity:** exact claim or image-event match versus topical or keyword overlap.
- **Provenance:** whether the item identifies a source, publication context, date, location, or original caption.
- **Cross-item agreement:** whether independent items converge or conflict.

Assign an overall strength:

- **Strong:** one authoritative and exact item, or at least two independent reputable items that converge on the material facts.
- **Moderate:** one reasonably reliable and specific item with no credible conflict, or several partial items that jointly establish the fact.
- **Weak:** search snippets without enough context, unattributed captions, social reposts, visual resemblance, generic topical overlap, or duplicated claims.
- **None:** no relevant evidence.

Only strong or moderate evidence can establish a decisive `Supported` or `Contradicted` finding. Weak evidence may guide interpretation but cannot by itself justify `Fake`. If reliable evidence conflicts, use `Conflicting` unless authority, specificity, provenance, and date clearly resolve the conflict. Do not count duplicated results as independent corroboration.

### Decision threshold

- A material failure is **established** when strong evidence, or converging moderate evidence, specifically supports it.
- A material failure is **plausible but unresolved** when only weak evidence or ambiguous model-based visual cues support it.
- A check **passes** when the material facts are specifically supported and no equally credible contradiction exists.
- A check is **unverified** when neither support nor contradiction reaches the threshold.

Do not treat lack of evidence as proof of falsity. In a forced binary benchmark, an item should not be labeled `Fake` solely because a check is unverified. State the uncertainty and decide from the strongest positive evidence available.

## Benchmark evidence mode

When the runner supplies pre-retrieved evidence:

- use only those evidence items and the attached image;
- do not perform or imply live search;
- do not assume an evidence item is true merely because it was retrieved;
- do not use filenames, sample IDs, dataset fields, or likely benchmark construction as evidence;
- keep direct and inverse evidence separate until reconciliation.

## Final reconciliation

Evaluate four independent questions:

1. Is the text factually supported?
2. Is the image authentic or materially manipulated?
3. Does the image depict the claimed person/event/details?
4. Do the retrieved sources support the image-text association?

Map the primary class as follows:

- `real`: all required checks pass.
- `textual_veracity_distortion`: the text is false or misleading while the image is not the primary problem.
- `visual_veracity_distortion`: the image is manipulated or factually abnormal while the text is not the primary problem.
- `cross-modal_consistency_distortion`: the text and image are individually plausible but are associated with different people, events, dates, places, or contexts.

If multiple failures are present, record secondary failures and select the primary class according to the strongest evidence and the evaluation label definition. Never hide a secondary failure merely to force a single class.

Use this causal tie-break when multiple failures have comparable evidence:

1. `textual_veracity_distortion` if the material proposition remains false even with an appropriate authentic image.
2. `visual_veracity_distortion` if the image itself is materially edited, composited, or generated and that visual alteration is the central deception.
3. `cross_modal_consistency_distortion` if the image is substantially authentic but is attached to the wrong person, event, place, date, or context.

When one candidate has clearly stronger and more specific evidence, choose it over this tie-break and record the others as secondary findings.
