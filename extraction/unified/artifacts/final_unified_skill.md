# Unified multimodal misinformation verification

## Purpose

Assess whether a news-like image and text claim belong together and whether
the supplied evidence supports the claim. The skill covers textual factuality,
visual veracity, and cross-modal consistency in one procedure. It must make
the distinction between “the event is real” and “this image is the image of
that event.”

The procedure is induced from TRUST-Instruct trajectories. It is an evidence
assessment workflow, not a license to fill gaps with world knowledge. Every
finding should identify what was observed, what it was compared with, and what
remains uncertain.

## Inputs and variables

- `{image}`: the image to assess;
- `{caption}`: the supplied text or news claim;
- `{direct_evidence}`: evidence used to check whether the image depicts the
  claimed event, person, object, or setting;
- `{inverse_evidence}`: evidence used to check whether the text claim matches
  the image’s actual subject, scene, or context;
- `{context_evidence}`: optional textual sources or context supplied by the
  task for factual support/refutation.

Keep these evidence roles separate. Do not treat a source that supports the
textual event as proof that the supplied image shows that event.

## Core workflow

### 1. Decompose the claim before looking for agreement

Parse `{caption}` into a structured `{claim_elements}` record:

```text
entities: people, organizations, species, objects
event: what happened
interaction: who did what to whom/with what
setting: place, venue, landmark, environment
time: date, period, sequence
attributes: appearance, quantity, role, affiliation, medium, status
claim_type: factual event, description, attribution, opinion, satire/parody
```

Do not collapse an event into a topic. “A politician at a campaign event,”
“that politician applauding a specific person,” and “that politician at this
date and venue” are different claim elements. If the caption has too few
elements to identify what would count as a visual match, mark
`claim_parse = incomplete` and carry that uncertainty forward.

### 2. Describe the image independently

Produce `{image_description}` without using the caption as a template. Record:

- visible people, objects, species, text, symbols, and landmarks;
- actions and specific interactions;
- setting and environmental cues;
- visual identifiers that could tie the image to an entity or event;
- attributes relevant to the claim, such as age, clothing, object type, or
  affiliation;
- whether the image appears to be a photograph, illustration, cartoon, or
  other medium;
- visible edit, compositing, or AI-generation cues.

Absence is not automatically contradiction. Record “not visible,” “not
identifiable,” or “contradicted” separately.

### 3. Check image-text consistency element by element

Compare `{image_description}` with `{claim_elements}` and assign each material
element one of:

- `match`: the visible content supports the element;
- `mismatch`: visible content contradicts the element or depicts a different
  entity, scene, event, or interaction;
- `inconclusive`: the image or claim lacks enough identifying information.

The overall image-text result must include a rationale. A shared location,
topic, or generic appearance is not enough when the claim depends on a named
person, exact event instance, date, role, or interaction.

### 4. Screen evidence relevance before comparison

For every item in `{direct_evidence}` and `{inverse_evidence}`, first classify
it as relevant or irrelevant.

- Relevant direct evidence is compared with `{image_description}`.
- Relevant inverse evidence is compared with `{claim_elements}`.
- Empty fields and off-topic items are `non-contributing`, not contradictions.
- Record the result for each contributing item as `supports`, `contradicts`,
  or `uncertain`.

Direct evidence can establish that an event occurred while failing to establish
that the supplied image shows that event. Inverse evidence can identify the
actual scene or subject of the image and therefore expose a wrong image-text
pairing.

### 5. Run modality-specific screens when triggered

#### Textual factuality screen

Use `{context_evidence}` to check names, attribution, event details, dates,
quantities, and source claims. Distinguish evidence that supports the claim
from boilerplate, generic context, or a source that merely mentions a related
topic. Treat an apparently light tone as serious unless the text or evidence
supports a satire/parody interpretation. A direct refutation or false
attribution is a Fake signal even if the image is visually compatible.

#### Visual veracity screen

Check whether the image itself appears manipulated, generated, or materially
altered. Keep this separate from a genuine image used with the wrong caption.
An illustration or cartoon may be genuine but still contradict a caption that
claims to show a real event. Report the medium and manipulation finding
independently before aggregation.

#### Cross-modal visual-tie screen

When the claim names a person, object, place, or event, test whether the image
can be tied to that specific entity and event instance. Entity-level similarity
is insufficient when the claimed action or interaction differs. If the image
shows a different or contradictory interaction, classify the pairing as Fake
even if direct evidence confirms a related event.

## Decision branches and precedence

Apply the following branches in order. They describe observed dataset patterns,
not universal facts outside the supplied inputs.

1. **Material contradiction.** A direct factual refutation, a visibly
   contradictory image, a confirmed wrong entity/event pairing, or relevant
   inverse evidence identifying a different scene supports `Fake`.
2. **Manipulation.** If the image is materially manipulated or AI-generated in
   a way relevant to the claim, report the visual-veracity failure and use it
   as a `Fake` signal. Do not call ordinary ambiguity manipulation.
3. **Exact visual tie.** If the claimed entity and event-specific visual
   details align, and no relevant evidence contradicts them, the image-text
   relation supports `Real`. A generic setting match alone does not satisfy
   this branch.
4. **Neutral action absence.** If the claimed entity is identifiable and the
   setting is broadly compatible, but the claimed action is merely not visible
   rather than contradicted, do not automatically classify `Fake`. Use direct
   and inverse evidence to resolve the case.
5. **Inconclusive image-text check.** If the caption is too short, the image
   lacks identifiers, or the visual details cannot settle the comparison, rely
   on relevant evidence cross-checks. If those checks are insufficient, state
   `Insufficient` when the task permits it; otherwise emit the required binary
   label together with explicit uncertainty and do not claim visual proof.
6. **Partial mismatch.** A partial mismatch in direct evidence does not by
   itself override compatible overall context when inverse evidence supports
   the text setting. Conversely, if direct evidence confirms only that a
   setting exists and cannot tie the claimed entity or interaction to the
   image, the pairing remains unsupported and may be `Fake`.
7. **Inverse-scene override.** If inverse evidence positively matches the
   image’s setting, subject, location, event, or medium while contradicting the
   caption’s specific claim, treat this as evidence of cross-modal mismatch.
   It can override direct evidence that only confirms the general event.
8. **Evidence insufficiency.** Empty or irrelevant evidence cannot support a
   contradiction. With aligned image-text content and no contrary evidence,
   the dataset sometimes uses an alignment-only `Real` conclusion; mark that
   conclusion as lower-certainty than one supported by relevant context.

## Observed pattern map

| Pattern learned from trajectories | Operational instruction | Support examples |
|---|---|---|
| Six-step recurring pipeline | Parse text, describe image, compare modalities, check direct evidence, check inverse evidence, conclude | `431849-real`, `801666-real`, `424118-fake`, `6133-visual_veracity_distortion` |
| Empty evidence pools | Skip unavailable checks and record them as non-contributing | `431849-real`, `424118-fake`, `6133-visual_veracity_distortion`, `6225-visual_veracity_distortion` |
| Short/incomplete caption | Mark image-text comparison inconclusive and defer to evidence | `99167-real` |
| Irrelevant evidence | Filter it before aggregation; do not count it as refutation | `1682986-fake`, `111829-real` |
| Entity/event visual tie | Require the claimed entity and specific event or interaction, not just a shared topic | `125127-fake`, `89803-fake`, `167300-fake` |
| Neutral action absence | Missing visibility of an action is not the same as a contradictory action | `300990-real` |
| Inverse scene identification | A different scene or subject identified by inverse evidence supports Fake | `451561-fake`, `93322-fake`, `1567669-fake` |
| Partial mismatch weighting | Context alignment can outweigh a partial direct-evidence entity mismatch | `187828-real` |
| Visual attribute conflict | Conflicting attributes or absent entity identifiers weaken the image tie | `349545-fake`, `653252-face_attribute` |
| Context support/refutation | Relevant context strengthens Real or overrides alignment when it refutes the claim | `6031-Support_Multimodal`, `16724-Refute`, `6527-Refute` |
| Satire/tone handling | Do not infer satire from a light tone alone; classify it only when supported | `tone_satire_screening` support set in `rule_ledger.json` |
| Manipulation versus miscontext | Screen manipulation separately from a genuine image paired with the wrong claim | `653252-face_attribute`, `913-original`, `167300-fake` |

## Output contract

Return the following ordered fields and keep each finding tied to the supplied
input:

```text
Claim elements: {claim_elements}
Image description: {image_description}
Image-text consistency: match|mismatch|inconclusive — basis
Direct evidence: per-item support|contradict|uncertain|non-contributing
Inverse evidence: per-item support|contradict|uncertain|non-contributing
Textual factuality/context: supported|refuted|uncertain|not assessed — basis
Visual veracity: genuine|manipulated|AI-generated|uncertain|not assessed — basis
Cross-modal finding: tied|wrong entity|wrong event instance|wrong scene|uncertain
Uncertainty: unresolved checks and unavailable evidence
Judgement: Real|Fake [or Insufficient if permitted]
```

The rationale must identify the decisive signal, distinguish direct from
inverse evidence, and state when the result is alignment-only or evidence-
insufficient.

## Provenance and maintenance

The induction used 196 representatives covering 196 semantic groups: 40
cross-modal, 71 textual, and 85 visual. The complete machine-readable support
sets are in `rule_ledger.json`, `workflow_catalog.json`, and
`workflow_memory.jsonl`. The final skill should be revised only when a new
trajectory adds independent support, narrows a rule, or exposes a conflict.
Do not append a new near-duplicate workflow; merge it into the applicable
pattern and add its row ID to the support set.
