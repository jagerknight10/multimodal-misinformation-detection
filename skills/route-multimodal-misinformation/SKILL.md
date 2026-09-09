---
name: route-multimodal-misinformation
description: Route a multimodal news claim to one or more textual-factuality, visual-manipulation, or cross-modal-consistency specialist workflows and reconcile their findings in one model call.
---

# Route Multimodal Misinformation Checks

Select and execute the relevant specialist workflow or workflows within the current response. Routing is internal reasoning, not a separate model or tool call.

Use only the supplied caption, image, direct evidence, and inverse evidence. The evidence can be noisy. Apply the shared evidence-strength rubric supplied with this workflow, and never use filenames, sample identifiers, benchmark labels, or presumed dataset construction as evidence.

## Shared triage

Before routing:

1. Parse the caption into material people, actions, events, places, dates, quantities, quotations, and image-event association claims.
2. Describe the image independently, including subjects, actions, scene, visible text, landmarks, and possible artifact cues.
3. Summarize what direct evidence establishes about the textual event and what inverse evidence establishes about image provenance.
4. Mark preliminary signals as `Supported`, `Contradicted`, `Conflicting`, `Unverified`, or `Irrelevant`. Do not equate missing evidence with contradiction.

## Routing rules

Select one or more exact identifiers:

- `Check_textual_factuality` when direct evidence conflicts with a material proposition, the claim appears fabricated or falsely attributed, or satire/stance/framing may create a factual deception.
- `Check_visual_manipulation` when the image or provenance evidence suggests editing, compositing, expression alteration, object insertion/removal, or AI generation.
- `Check_cross_modal_consistency` when inverse provenance may identify another event, place, or date; when image and caption agree only topically; or when the caption makes a specific image-event association requiring verification.

For an apparently real item, choose the specialist most relevant to the main residual uncertainty; do not select every specialist mechanically. Select a second specialist when it tests a genuinely independent failure hypothesis. Select all three only when triage finds distinct textual, visual, and association signals. When uncertain between two adjacent classes, execute both relevant specialists in the same response.

Do not make separate model or tool calls. Execute only the selected procedures that are provided with this router.

## Reconciliation and primary class

For each selected specialist, retain `Established failure`, `No established failure`, or `Unresolved` and its evidence strength.

1. If exactly one specialist establishes a material failure, use its candidate class.
2. If several establish failures, choose the class supported by the most authoritative, independent, specific, and provenance-rich evidence. Record the others as secondary failures.
3. If evidence strength is comparable, use the causal boundary:
   - `textual_veracity_distortion`: the proposition remains false even with an appropriate authentic image;
   - `visual_veracity_distortion`: the image itself is materially altered/generated and that alteration is central;
   - `cross_modal_consistency_distortion`: a substantially authentic image is paired with the wrong context.
4. If no material failure is established, choose `real`. Do not choose `Fake` solely because evidence is absent, weak, or unresolved.

A `Real` judgment means no material textual, visual, or cross-modal failure is positively supported by the available image and evidence. It does not mean every incidental detail has been independently proven.

## Routed output contract

Keep the reasoning concise enough to finish the required fields:

```text
Shared analysis: <material caption facts and independent image description>
Routing rationale: <why each selected specialist is relevant>
Specialist findings:
- <specialist>: <result, strongest evidence, and strength>
Evidence reconciliation: <primary and any secondary failures; unresolved points>
Primary failure: <none or one benchmark class>
Confidence: <High | Medium | Low>
Selected skills: <comma-separated exact specialist identifiers>
Judgement: <Real | Fake>
Class: <real | textual_veracity_distortion | visual_veracity_distortion | cross_modal_consistency_distortion>
```

Always report at least one selected specialist. The final `Judgement` and `Class` must agree: `Real` only with class `real`; every distortion class requires `Fake`.
