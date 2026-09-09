---
name: check-textual-factuality
description: Check whether a news caption's factual claims are supported, contradicted, or unresolved by supplied text-led and image-led evidence. Use as a specialist workflow for textual misinformation in multimodal news verification.
---

# Check Textual Factuality

Evaluate whether the caption's material propositions are factual and appropriately framed. This is the TRUST-VL textual branch: claim analysis, linguistic-pattern analysis, and evidence support. During benchmark evaluation, use only the supplied image and pre-retrieved evidence; do not perform or imply live search.

Apply the shared evidence-strength rubric supplied with the routing workflow. Do not infer truth from retrieval rank, repeated wording, filenames, or benchmark metadata.

## Textual verification procedure

1. **Decompose the caption.** List the atomic claims about identity, action, event, place, time, quantity, quotation, cause, and attribution. Separate explicit claims from implications and opinions.
2. **Identify materiality.** Mark which claims would substantially change the news event if false. Incidental wording, harmless imprecision, and unverifiable decorative details are not primary distortions.
3. **Assess tone and stance.** Note satire, sarcasm, sensational wording, unsupported certainty, impersonation, or misleading framing. Tone is diagnostic context, not proof of falsity. An opinion is not false merely because it is negative.
4. **Adjudicate direct evidence claim by claim.** For each material claim, identify the strongest relevant item, its source quality if available, its specificity, and whether it is `Supported`, `Contradicted`, `Conflicting`, `Unverified`, or `Irrelevant`.
5. **Use inverse evidence carefully.** Use image-led evidence to clarify identities, dates, locations, original captions, or events only when it bears directly on the textual proposition. Do not silently turn an image-caption mismatch into a textual failure.
6. **Resolve conflicts.** Prefer exact, contemporaneous, attributable evidence over generic, undated, copied, or merely similar material. Keep `Unverified` distinct from `Contradicted`.
7. **Determine the textual result.**
   - `Established failure`: strong or converging moderate evidence shows a material proposition is fabricated, false, materially misleading, or falsely attributed.
   - `No established failure`: material propositions are supported and no equally credible contradiction exists.
   - `Unresolved`: evidence is missing, weak, or conflicting. This alone is not grounds for `Fake`.

## Classification boundary

Recommend `textual_veracity_distortion` only for an established material textual failure that remains false regardless of whether the attached image is appropriate. A claim that an image depicts a specific event is an association claim; if the event itself is real but the image comes from elsewhere, route that failure to `Check_cross_modal_consistency`.

## Boundaries

- If the caption is plausible but the authentic image comes from another event, defer the primary diagnosis to `Check_cross_modal_consistency`.
- If the main problem is an edited or generated image, defer it to `Check_visual_manipulation`.
- Do not infer the benchmark label from filenames, sample IDs, or metadata.

## Specialist output

Return a compact block for the router:

```text
Text claims: <material atomic claims>
Text evidence: <claim -> strongest evidence -> status and strength>
Tone/stance: <relevant linguistic pattern or none>
Text result: <Established failure | No established failure | Unresolved>
Text candidate class: <textual_veracity_distortion | none>
Text rationale: <one or two evidence-grounded sentences>
```
