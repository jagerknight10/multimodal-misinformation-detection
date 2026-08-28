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
