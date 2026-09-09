---
name: check-cross-modal-consistency
description: Check whether a news image depicts the exact people, event, place, and time claimed by its caption using supplied direct and inverse evidence. Use for out-of-context and image-caption mismatch misinformation.
---

# Check Cross-Modal Consistency

Evaluate the exact image-caption association, not merely whether each modality is plausible in isolation. This is the TRUST-VL cross-modal branch: image↔caption, image↔direct-evidence, and caption↔inverse-evidence consistency. During benchmark evaluation, use only the supplied image and pre-retrieved evidence; do not perform or imply live search.

Apply the shared evidence-strength rubric supplied with the routing workflow. Broad topical similarity, visual resemblance, and missing provenance are not sufficient to establish an event match or mismatch.

## Cross-modal verification procedure

1. **Extract the caption account.** Record claimed identity, action, event, place, date, organization, objects, and the implied statement that this image depicts that event.
2. **Extract the image account independently.** Record only visible or evidence-supported identity, action, setting, signs, landmarks, OCR text, weather, and temporal clues. Do not import caption details into the image description.
3. **Establish the captioned event.** Use direct evidence to determine whether the stated event occurred and what its reliable accounts say. A real event does not prove that the attached image depicts it.
4. **Establish image provenance.** Use inverse evidence to identify the exact or near-exact image's source, original caption, event, date, and location. Distinguish exact matches from similar images.
5. **Run three explicit comparisons.**
   - `Image ↔ caption`: compare visible identity, action, setting, objects, and event details.
   - `Image ↔ direct evidence`: determine whether evidence about the captioned event describes or contains this image context.
   - `Caption ↔ inverse evidence`: determine whether the image's provenance agrees with the caption's person, event, place, and time.
6. **Build a field matrix.** For identity, action, event, place, and time, mark `Match`, `Conflict`, or `Unresolved`, and cite the strongest supplied basis.
7. **Determine the cross-modal result.**
   - `Established failure`: strong or converging moderate evidence ties the image to a materially different person, event, place, date, or context.
   - `No established failure`: material fields match and provenance/evidence provides adequate support.
   - `Unresolved`: event association cannot be established either way. This alone is not grounds for `Fake`.

## Classification boundary

Recommend `cross_modal_consistency_distortion` when the image is substantially authentic but the association is materially wrong. If the proposition itself remains false with any appropriate image, use textual distortion. If the central deception is a materially altered or generated image, use visual distortion.

## Boundaries

- Missing provenance is `Unverified`, not automatically a mismatch.
- If the caption itself is demonstrably false regardless of the image, consider `Check_textual_factuality`.
- If the image itself is materially edited or generated, consider `Check_visual_manipulation`.
- Do not infer the benchmark label from filenames, sample IDs, or metadata.

## Specialist output

Return a compact block for the router:

```text
Caption account: <identity, action, event, place, time>
Image account: <independent visible/evidence-supported account>
Consistency matrix: <field -> Match | Conflict | Unresolved -> strongest basis>
Provenance: <original image context or unresolved>
Cross-modal result: <Established failure | No established failure | Unresolved>
Cross-modal candidate class: <cross_modal_consistency_distortion | none>
Cross-modal rationale: <one or two evidence-grounded sentences>
```
