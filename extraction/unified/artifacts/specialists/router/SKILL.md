# Route multimodal misinformation

## Purpose
Route an input to one or more provenance-backed distortion specialists. The router selects specialists; it does not make the final judgement.

## Routing rules

- Route to `Check_textual_factuality` when the central question concerns whether the caption's people, event, date, attribution, quantity, or context is factually supported or refuted.
- Route to `Check_visual_manipulation` when the central question concerns image editing, AI generation, visual artifacts, medium, or the image's own veracity.
- Route to `Check_cross_modal_consistency` when the question concerns whether this image depicts the captioned person, event, interaction, place, or context, including direct/inverse evidence comparisons.
- Route to multiple specialists when the task combines textual factuality, visual integrity, and image-text pairing.
- If the task is ambiguous, route to cross-modal plus the specialist suggested by the explicit evidence fields, and preserve the uncertainty.

## Handoff
Pass the original image, caption, relevant evidence fields, the selected specialist names, and the reason for each selection. Each specialist must return its own findings before final aggregation.
