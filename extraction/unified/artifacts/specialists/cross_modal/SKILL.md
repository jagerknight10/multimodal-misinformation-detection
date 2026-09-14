# Check_cross_modal_consistency

## Scope

Assess image-text and bidirectional evidence consistency using only the supplied task inputs and evidence.

## Required inputs

- image (when supplied)
- caption or text claim
- direct, inverse, or context evidence when supplied

## Procedure

1. Extract the task-specific claim or visual facts.
2. Apply the reusable workflows below in their stated order.
3. Record support, contradiction, non-contribution, and uncertainty separately.
4. Return the required verdict with a concise evidence-linked rationale.

## Extracted workflows

### judgement_aggregation
Aggregate consistency and evidence results into a final Real/Fake judgement.
Steps: Apply hard overrides: contradictory depicted interaction, or image matching an inverse-evidence scene -> Fake.; If image-text consistency is inconclusive, rely on evidence cross-checks.; If direct evidence confirms the event and inverse evidence has no contradictions -> Real.; Emit the final Real/Fake judgement with the deciding factors.
Conditions: Partial entity mismatch in direct evidence with aligned context and clean inverse evidence -> does not override Real.; No hard override and evidence aligned -> Real.
Output: Final label Real|Fake plus the deciding evidence factors.
Support: 111829-real, 1488781-real, 1102464-real, 1080184-fake, 1589261-real, 198663-fake, 400247-fake, 1185433-real, 450468-fake, 198663-real, 213108-real, 62591-real, 822340-real, 43627-real, 45926-real, 837138-real, 99167-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 597755-fake, 98106-real, 105708-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 272321-fake, 1682986-fake, 637499-real, 1682986-real, 576980-fake, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 205992-fake, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 1117352-real, 298661-real, 885904-fake, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real

### image_text_consistency_check
Determine whether the image visually supports the text claim
Steps: Map visual elements of {image_description} to {claim_elements}; Judge match, mismatch, or inconclusive; For vague text, assess whether the image depicts a real event or a staged/edited scene
Conditions: no identifiable context for the claimed event -> mismatch; staged or edited appearance -> flag as non-factual
Output: consistency verdict (match/mismatch/inconclusive) with cited visual elements
Support: 431849-real, 801666-real, 868253-real, 111829-real, 1488781-real, 1102464-real, 1589261-real, 198663-fake, 213108-real, 62591-real, 822340-real, 43627-real, 45926-real, 837138-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 597755-fake, 105708-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 1682986-fake, 637499-real, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 298661-real, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real, 424118-fake, 6133-visual_veracity_distortion, 6225-visual_veracity_distortion

### evidence_cross_check
Cross-check the image against direct evidence and the text against inverse evidence.
Steps: For each direct evidence item, assess relevance to the image (event, venue, entities).; For each inverse evidence item, assess relevance to the text and whether it contradicts or corroborates the claim.; Skip empty or off-topic items as non-contributing.; Record per item: contradiction, corroboration, or partial entity mismatch.
Conditions: Item empty or off-topic -> non-contributing, not a contradiction.; Inverse item corroborates the claim -> non-contradictory.; Image setting or visual details match an inverse-evidence scene -> item is image-relevant.
Output: Per-item flags: relevant|non_contributing and corroborates|contradicts|partial_mismatch.
Support: 111829-real, 1488781-real, 1102464-real, 1589261-real, 198663-fake, 400247-fake, 1185433-real, 213108-real, 822340-real, 43627-real, 45926-real, 837138-real, 99167-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 98106-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 272321-fake, 1682986-fake, 1682986-real, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 205992-fake, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 1117352-real, 298661-real, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real

### image_content_description
Produce a structured description of the image for comparison against the claim and evidence
Steps: Identify {image_subjects} and their visible actions; Describe {image_setting} and environment; Record presence/absence of each {claimed_element}; Note visual identifiers (species, landmarks, people, text)
Conditions: Image lacks visual identifiers -> mark low-identifiability
Output: Structured description: subjects, setting, claimed-element presence/absence, identifiers
Support: 431849-real, 801666-real, 868253-real, 198663-fake, 1185433-real, 213108-real, 45926-real, 837138-real, 322977-fake, 199432-real, 597755-fake, 146372-fake, 410258-fake, 982456-real, 1236343-real, 298661-real, 582078-fake

### claim_element_parsing
Decompose the caption into atomic, verifiable claim elements
Steps: Read the caption text; Extract {claimed_subject}, {claimed_action}, {claimed_setting}, {claimed_location}; Flag the caption as low-information if it lacks verifiable identifiers
Conditions: Caption too short or missing identifiers -> mark low-information for downstream consistency check
Output: Structured claim elements: subject, action, setting, location
Support: 1080184-fake, 1589261-real, 198663-fake, 198663-real, 45926-real, 199432-real, 143664-real, 146372-fake, 410258-fake, 982456-real, 47981-real, 462287-real, 582078-fake

### image_description
Produce a factual image description usable for comparison
Steps: Identify visible {entities} and their {actions}; Describe {setting} and visual identifiers (flags, venue, objects); Note identifiers that could anchor or contradict the claim
Conditions: Image lacks visual identifiers -> flag for inconclusive consistency
Output: Structured description: entities, actions, setting, identifiers
Support: 198663-real, 143664-real, 1221030-real, 272321-fake, 1682986-real, 199961-fake, 47981-real, 139570-fake, 816513-real, 1117352-real, 235782-fake, 462287-real

### claim_decomposition
Parse the caption into verifiable claim elements before any cross-modal comparison.
Steps: Extract named entities (people, organizations) from the caption.; Extract the claimed event, setting, and action/interaction if present.; Flag elements too short or vague to verify visually.
Conditions: Caption lacks explicit event or action -> mark those elements unverifiable from text alone.
Output: Structured claim elements: entities[], event, setting, action, verifiability flags.
Support: 1102464-real, 62591-real, 98106-real, 1221030-real, 272321-fake, 199961-fake, 595563-real, 791248-fake, 139570-fake, 235782-fake, 179993-real

### cross_modal_verification_pipeline
Judge whether a news image is used correctly in its caption context (Real/Fake) by combining image-text consistency with evidence cross-checks.
Steps: Parse the caption into claim elements (entities, action, setting, purpose).; Describe the image in detail and assess image-text consistency; mark inconclusive if the caption is too short or the image lacks visual identifiers.; Cross-check the image against each direct evidence item, skipping empty or irrelevant items.; Cross-check the text against each inverse evidence item, skipping empty or irrelevant items.; Aggregate consistency and evidence results into a Real/Fake judgement with per-step reasoning.
Conditions: If image-text consistency is inconclusive, rely on evidence cross-checks for the judgement.; If the image depicts a different or contradictory interaction than the claimed one, judge Fake even when direct evidence confirms the event.; If the image is neutral (claimed entity identifiable, setting broadly consistent, claimed action merely absent), rely on evidence cross-checks and judge Real when direct evidence confirms the event and inverse evidence has no contradictions.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.; Irrelevant or off-topic evidence items are treated as non-contributing, not as contradictions.
Output: Real/Fake judgement with step-by-step reasoning covering text analysis, image description, consistency, and both evidence cross-checks.
Support: 514577-real, 272289-real, 206694-real, 146372-real, 246181-real, 940097-real, 50978-fake, 404887-fake, 300990-real, 208379-real

### image_text_consistency_assessment
Assess whether image content aligns with the text claim
Steps: Extract {claim_elements} (entities, event, location, date) from {text_claim}; Describe {image} main subject and scene; Assess alignment between {image} and {claim_elements}
Conditions: identities unconfirmable -> note uncertainty; scene matches event type -> consistent
Output: {consistency_finding}: {match, mismatch, uncertain}
Support: 89803-fake, 460533-real, 885904-fake, 653252-face_attribute, 593986-face_swap, 913-original

### judgment_aggregation
Combine all consistency and evidence cross-check results into a final Real/Fake judgment
Steps: Review all consistency and evidence check results; Apply rules: inconclusive image-text consistency → rely on evidence cross-checks; partial entity mismatch with irrelevant inverse evidence → Fake; Determine final judgment: Real or Fake
Conditions: If image-text consistency is inconclusive, weight evidence cross-checks more heavily; If direct evidence has partial mismatch and inverse evidence is irrelevant, judge Fake; If all checks align, judge Real
Output: Real or Fake judgment with aggregated reasoning
Support: 424118-fake, 1003172-real, 187828-real, 89803-fake, 460533-real

### claim_and_image_grounding
Establish claim elements and visual grounding before evidence checks.
Steps: Parse the caption into claim elements: entities, event, location, date.; Describe the image in detail, noting visual identifiers (architecture, people, objects).; Compare the image description with the claim elements and record consistency.
Conditions: Caption too short or image lacks visual identifiers -> mark image-text consistency inconclusive.
Output: Claim element list, image description, image-text consistency status (consistent / inconsistent / inconclusive).
Support: 111829-real, 1488781-real, 307680-fake, 545751-real, 205992-fake

### claim_element_decomposition
Parse the caption into discrete verifiable claim elements
Steps: Extract {actor}, {action}, {target}, {location}, {date} from {caption}; Record each element as a discrete claim for downstream verification
Conditions: If {caption} is too short to yield discrete elements, mark the claim as under-specified
Output: List of claim elements {actor, action, target, location, date}
Support: 822340-real, 322977-fake, 98106-fake, 1682986-fake, 298661-real

### image_text_consistency
Determine whether the image supports, contradicts, or is inconclusive for the claim
Steps: Compare claim elements against image description; Classify as consistent, contradictory, or inconclusive; If contradictory interaction, mark Fake-leaning; if neutral, defer to evidence
Conditions: Caption too short or image lacks identifiers -> inconclusive; Contradictory interaction -> Fake even if direct evidence confirms; Neutral image -> rely on evidence cross-checks
Output: Consistency label (consistent/contradictory/inconclusive) with rationale
Support: 99167-real, 98106-real, 272321-fake, 1682986-real, 1117352-real

### claim_parsing_and_image_description
Establish the text claim baseline and an independent image description before comparison
Steps: Parse text into claim elements {claim_elements} (entities, event, location, date); Produce a detailed image description {image_description} independent of the text; Flag vague or humorous text as lacking concrete claim elements
Conditions: vague/humorous text -> mark claim elements as insufficient for factual comparison
Output: {claim_elements}, {image_description}
Support: 1553640-real, 431849-real, 424118-fake, 6133-visual_veracity_distortion, 6225-visual_veracity_distortion

### cross_modal_consistency_check
Verify consistency between image, caption, and evidence
Steps: Compare image description against claim elements; Compare image against direct evidence captions; Compare caption against inverse evidence items
Conditions: Skip direct-evidence check if direct evidence is empty; Skip inverse-evidence check if inverse evidence is empty
Output: Per-check consistency verdict (consistent / inconsistent / not checked)
Support: 1080184-fake, 1185433-real, 450468-fake, 198663-real

### claim_element_extraction
Decompose the caption into discrete verifiable claim elements.
Steps: Identify claimed entities, locations, events, actions, and time references in the caption; Record each element as a separate checkable fact
Conditions: If the caption is too short to yield checkable elements, flag the claim as under-specified
Output: List of claim elements (entity, location, event, action, time)
Support: 1185433-real, 43627-real, 837138-real, 816513-real

### bidirectional_evidence_cross_check
Verify the image against direct evidence and the text against inverse evidence
Steps: For each direct evidence item, check whether the image matches the described entity/setting/event; For each inverse evidence item, check whether the text claim is contradicted; Skip empty or off-topic items and mark them non-contributing; Record matches, mismatches, and non-contributing items
Conditions: Partial entity mismatch (different person at same venue) does not override overall context alignment; Off-topic items are non-contributing, not contradictions
Output: Per-evidence-item match/mismatch/non-contributing summary
Support: 597755-fake, 105708-real, 637499-real, 885904-fake

### evidence_pool_cross_check
Cross-check image and text against direct and inverse evidence pools
Steps: Check {direct_evidence_pool} for relevance; compare relevant items to {image_description}; Check {inverse_evidence_pool} for relevance; compare relevant items to {claim_elements}; If a pool is empty or all items irrelevant, record it as non-contributing and skip
Conditions: empty pool -> skip and note absence; irrelevant items -> non-contributing
Output: per-pool finding (support/contradict/non-contributing) or 'no evidence'
Support: 431849-real, 424118-fake, 6133-visual_veracity_distortion, 6225-visual_veracity_distortion

### verdict_aggregation
Combine consistency findings into a final Real/Fake judgement
Steps: Aggregate image-text and evidence-pool findings; Apply mismatch rules (visual tie, inverse-scene match, attribute conflict) when evidence exists; Emit {judgment} with rationale citing decisive findings and noting absent evidence
Conditions: evidence pools empty -> rely on image-text consistency alone; all findings consistent -> Real; confirmed mismatch -> Fake
Output: {judgment} in {Real, Fake} plus cited rationale
Support: 431849-real, 424118-fake, 6133-visual_veracity_distortion, 6225-visual_veracity_distortion

### text_claim_analysis
Extract verifiable claim elements from the caption
Steps: Parse caption text; Identify entities, event, date, location, quantities; Formulate the claim to verify
Output: structured claim summary
Support: 431849-real, 801666-real, 868253-real

### evidence_consistency_check
Cross-check image vs direct evidence and text vs inverse evidence
Steps: If direct evidence present, compare image to it; If inverse evidence present, compare text to it; Note 'no evidence' for empty fields
Conditions: Skip check when corresponding evidence is empty
Output: per-evidence verdict or 'no evidence'
Support: 431849-real, 801666-real, 868253-real

### final_judgement_aggregation
Aggregate consistency results into a final label
Steps: Summarize consistency findings; Weigh image-text and evidence results; Emit judgement
Conditions: Any contradiction supports Fake; all consistent supports Real
Output: Judgement: Real|Fake
Support: 431849-real, 801666-real, 868253-real

### text_image_consistency_assessment
Determine whether the image matches the text description
Steps: Parse caption into claim elements (entities, events, locations, dates); Generate detailed visual description of the image; Compare image description against text claim elements for consistency
Conditions: Always executed
Output: Consistent or Inconsistent with reasoning
Support: 424118-fake, 1003172-real, 187828-real

### evidence_cross_verification
Cross-check image and text against provided evidence
Steps: If direct evidence is present, check image consistency against it; If inverse evidence is present, check text consistency against it; Skip any evidence check if the evidence field is empty
Conditions: Skip direct evidence check if empty; Skip inverse evidence check if empty
Output: Per-evidence consistency assessment or 'no evidence provided'
Support: 424118-fake, 1003172-real, 187828-real

### Cross-modal verification pipeline
Determine Real/Fake by systematically comparing text claims against image content and available evidence.
Steps: Parse caption into claim elements (entity, action, setting, temporal); Produce detailed image description (objects, people, setting, edit cues); Assess image-text consistency (do visual elements support the text's claims); Cross-check image against direct evidence items (if any provided); Cross-check text against inverse evidence items (if any provided); Aggregate all consistency signals into a Real/Fake judgement with step-by-step reasoning
Conditions: Skip direct-evidence step when no direct evidence is supplied; Skip inverse-evidence step when no inverse evidence is supplied; If inverse evidence aligns with the image's generic setting but not the text's specific entity claim, treat as a signal that the text's specific claims are unsupported
Output: Ordered step-by-step analysis followed by a final Real/Fake judgement
Support: 6133-visual_veracity_distortion, 6225-visual_veracity_distortion, 693635-fake

### caption_claim_decomposition
Decompose the caption into verifiable claim elements
Steps: Extract entities and actions from the caption; Extract location and time references; List claim elements for downstream checks
Conditions: If the caption is too short to verify, mark it inconclusive
Output: List of claim elements {entities, actions, location, time}
Support: 213108-real, 597755-fake, 1236343-real

### direct_evidence_image_cross_check
Verify the image against direct evidence items
Steps: Enumerate direct evidence items; Skip empty or irrelevant items; Compare image entities and setting against evidence; Note when evidence supports the claim but lacks visual detail
Conditions: Empty or irrelevant evidence items are skipped
Output: support status: supports | contradicts | no visual detail
Support: 89803-fake, 460533-real, 576980-fake

### inverse_evidence_text_cross_check
Check the text against inverse evidence for contradictions
Steps: Enumerate inverse evidence items; Treat off-topic items as non-contributing; Compare claim setting against inverse evidence contexts; Flag contradiction only on direct conflict with the claim
Conditions: Off-topic items are non-contributing, not contradictions
Output: contradiction status: contradicts | no contradiction
Support: 89803-fake, 460533-real, 576980-fake

### image_scene_description
Produce a detailed structured description of the image for comparison.
Steps: Identify main subjects and objects {subjects, objects}.; Identify setting/venue cues {venue_cues}.; Identify weather and lighting {weather, lighting}.; Identify contextual props (tents, crowds, signage) {context_cues}.
Conditions: Image is present
Output: structured {image_description}
Support: 1080184-fake, 1682986-fake

### claim_decomposition_and_image_description
Extract structured claim elements from text and generate a detailed image description for downstream checks
Steps: Parse text into claim elements: person, event, date, location, action; Describe image in detail: subject, setting, objects, context, visual cues
Conditions: Always executed as first step
Output: Structured claim elements + free-text image description
Support: 89803-fake, 460533-real

### Cross-modal misinformation verification pipeline
Determine whether a caption-image pair contains cross-modal misinformation by grounding the claim in the image and cross-checking both against provided evidence.
Steps: Parse the caption into claim elements (people, work, event, date, setting).; Describe the image's scene, attire, setting, and any identifiable entities.; Assess image-text consistency against the claim elements.; Cross-check the image against direct evidence and the text against inverse evidence, skipping empty evidence.; Aggregate the consistency signals into a Real/Fake judgement with a stated reason.
Conditions: Skip an evidence cross-check when the corresponding evidence is empty.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.; If inverse evidence attributes the image to a different source than the caption claims, treat it as a source mismatch.
Output: A Real/Fake judgement with a brief justification citing the decisive consistency signal.
Support: 410430-fake

### cross_modal_claim_verification
Judge whether a news image matches its caption by combining image-text consistency with direct and inverse evidence cross-checks.
Steps: Parse the caption into claim elements: actors, event, setting, and date.; Describe the image and identify visible entities, activity, and setting.; Compare image entities and setting against the caption's claim elements for consistency.; Cross-check the image against direct evidence and the caption against inverse evidence, skipping any empty evidence set.; Aggregate all consistency results into a Real/Fake judgement with a rationale.
Conditions: If image entities or event contradict the caption's claim, flag the image as out of context.; Skip the direct-evidence or inverse-evidence check when that evidence set is empty.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.
Output: Real/Fake judgement with step-by-step rationale covering image-text consistency, direct-evidence check, and inverse-evidence check.
Support: 127382-fake

### Cross-modal claim-image verification
Decide whether a news image is faithful to its caption by cross-checking both against direct and inverse evidence.
Steps: Parse the caption into claim elements (actors, action, location, event, time).; Describe the image content in detail.; Assess image-text consistency against the claim elements.; Cross-check the image against direct evidence and the text against inverse evidence, skipping any empty evidence.; Aggregate the consistency signals into a Real/Fake judgement with a brief justification.
Conditions: If the image and text describe different events, judge Fake.; Skip empty direct or inverse evidence rather than treating absence as a signal.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.
Output: A Real/Fake judgement plus a short justification citing which evidence supported the image vs the text.
Support: 113060-fake

### claim_and_image_analysis
Produce structured inputs for cross-modal comparison by extracting claim elements and describing the image.
Steps: Parse the caption into claim elements (location, entity, setting, date).; Describe the image in detail (content, perspective, key visual features).
Output: Structured claim elements plus a detailed image description.
Support: 450468-fake

### claim_image_grounding
Extract claim elements from the caption and describe the image to establish comparable facts before consistency checks
Steps: Parse the caption into claim elements (subject, role, event, time, location); Describe the image (subject, action, setting, context)
Conditions: Caption too short to verify -> mark image-text consistency as inconclusive
Output: Structured claim elements + image description
Support: 164672-fake

### consistency_evidence_judgement
Determine image-text consistency, cross-check against direct and inverse evidence, and aggregate into a Real/Fake judgment
Steps: Compare image description with caption claims -> consistent/inconsistent/inconclusive; Cross-check image against direct evidence (skip if empty); Cross-check text against inverse evidence (skip if empty); Aggregate all signals into a Real/Fake judgment
Conditions: Image-text inconclusive -> rely on evidence cross-checks; Partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting
Output: Real/Fake judgment with reasoning
Support: 164672-fake

### claim_decomposition_and_image_text_consistency
Determine whether the image supports the caption's claim elements
Steps: Parse the caption into claim elements (entities, action, location, time/event); Describe the image content in detail; Compare image content against each claim element; Mark inconclusive if the image does not clearly indicate the claimed location or event
Conditions: Image ambiguous about location/event -> inconclusive, not inconsistent
Output: consistency status: consistent | inconsistent | inconclusive
Support: 576980-fake

### cross_modal_misinformation_verification
Determine whether a news image supports or contradicts its caption's claim by combining image-text consistency with evidence cross-checks
Steps: Parse the caption into claim elements (entities, roles, expected event); Describe the image in detail (people, setting, actions, visual identifiers); Check image-text consistency; mark inconclusive if the caption is too short or the image lacks visual identifiers; Cross-check the image against direct evidence and the text against inverse evidence, skipping empty or irrelevant items; Aggregate the consistency results into a Real/Fake judgement
Conditions: If the image depicts a different or contradictory interaction than the claimed one, judge Fake even if direct evidence confirms the event; If the image is neutral (claimed entity identifiable, setting broadly consistent, claimed action absent but not contradicted), rely on evidence cross-checks; If the image aligns with the inverse-evidence context, treat it as corroboration of the image-text mismatch
Output: Real/Fake judgement with per-check reasoning
Support: 1505500-fake

### claim_and_image_parsing
Extract verifiable elements from the caption and a detailed description of the image.
Steps: parse caption into claim_elements (actors, action, location, time); describe image: people, objects, setting, activity, atmosphere
Output: claim_elements list plus structured image_description
Support: 451561-fake

## Extracted decision rules

### image_text_consistency_check
Determine whether the image faithfully depicts the claim in the caption
Triggers: caption text and image both present
Steps: Compare depicted entities, setting, and attributes against claim elements; Record consistency verdict with rationale
Conditions: Flag inconsistent if visual elements contradict the claim
Evidence Rules: Use only observed visual elements and stated claim elements; no external knowledge
Decision Criteria: All key claim elements plausibly represented in image
Uncertainty: Ambiguous or low-detail images where claim elements cannot be confirmed or refuted
Support: 431849-real, 801666-real, 868253-real

### evidence_consistency_check
Cross-check image against direct evidence and text against inverse evidence
Triggers: direct or inverse evidence field non-empty
Steps: If direct evidence present, compare image to it; If inverse evidence present, compare text to it; Note 'no evidence' when a field is empty
Conditions: Skip direct-evidence check when empty; Skip inverse-evidence check when empty
Evidence Rules: Treat evidence entries as reference items only; do not assume unprovided content
Decision Criteria: No contradiction between image and direct evidence, or text and inverse evidence
Uncertainty: Evidence sources that are non-visual or unverifiable from the image
Support: 431849-real, 801666-real, 868253-real

### final_judgement_aggregation
Aggregate consistency findings into a final label
Triggers: all consistency checks complete
Steps: Summarize prior consistency findings; Emit final judgement label
Conditions: Contradiction in any check supports Fake; all consistent supports Real
Evidence Rules: Judgement must cite the consistency results, not external facts
Decision Criteria: Overall alignment of image, text, and available evidence
Uncertainty: Mixed or inconclusive consistency signals
Support: 431849-real, 801666-real, 868253-real

### evidence_relevance_filter
Prevent off-topic evidence items from distorting cross-checks
Triggers: evidence pool contains items unrelated to the claim's entities, events, or setting
Steps: Extract claim elements (entities, events, dates, locations); Filter each evidence item for relevance to claim elements; Treat irrelevant items as non-contributing (neither supporting nor contradicting); Cross-check only relevant items against the image (direct) or text (inverse)
Conditions: If all items in a pool are irrelevant, record the pool as non-contributing and continue
Evidence Rules: Irrelevant evidence is neither supporting nor contradicting; Relevant direct evidence is matched against image content; relevant inverse evidence against text claim elements
Decision Criteria: A pool contributes only if at least one item is relevant to the claim
Uncertainty: Relevance of ambiguous items (e.g., generic terms) is judged by co-occurrence with claim-specific entities
Support: 1682986-real

### unconfirmed_entity_image_fake
Resolve inconclusive image-text consistency when direct evidence confirms only the setting, not the claimed entities
Triggers: image-text consistency inconclusive due to missing visual identifiers; direct evidence supports setting but lacks entity confirmation
Steps: mark image-text consistency inconclusive when the image lacks identifiers for claimed persons or location; check whether direct evidence confirms setting and/or entities; treat irrelevant inverse evidence as non-contributing; judge Fake if the image cannot be visually tied to the claimed entities despite setting support
Conditions: direct evidence confirms setting but not entities; inverse evidence irrelevant
Evidence Rules: setting-only support from direct evidence is a weak positive, not entity confirmation; irrelevant inverse evidence is non-contributing, not contradicting
Decision Criteria: absence of visual confirmation of claimed entities in the image yields Fake when consistency is inconclusive
Uncertainty: cases where direct evidence visually confirms entities but consistency is inconclusive for other reasons
Support: 199961-fake

### inverse_scene_match_override
Judge Fake when the image's setting or visual details positively match an inverse-evidence scene (different location/event), even if direct evidence supports the text.
Triggers: image visual details align with an inverse-evidence scene; direct evidence supports the text but not the image's visual details
Steps: compare image setting, objects, and people against inverse-evidence scenes; verify direct evidence does not describe the image's distinctive visual details; flag image-source mismatch; judge Fake with rationale citing the inverse-scene match
Conditions: inverse evidence is on-topic and matches the image (not irrelevant); claimed action may be present (e.g., fire) while the setting differs
Evidence Rules: inverse evidence matching the image is image-relevant, not non-contributing; direct evidence supporting the text does not override an image-source mismatch
Decision Criteria: image matches the inverse scene better than the claimed scene -> Fake
Uncertainty: image partially matches both the claimed and an inverse scene
Support: 451561-fake

### empty_evidence_pools
Define judgement behaviour when both evidence pools are empty
Triggers: direct and inverse evidence pools are empty
Steps: Skip direct and inverse cross-checks and record them as unavailable; Base the judgement solely on image-text consistency; State in the rationale that no evidence was available
Conditions: both pools empty -> image-text consistency is the sole signal
Evidence Rules: empty pools are non-contributing, not contradictions
Decision Criteria: image-text match with aligned event context -> Real; image lacks identifiable context for the claimed event -> Fake
Uncertainty: staged/edited images with vague text: consistency alone may not establish veracity
Support: 431849-real, 424118-fake, 6133-visual_veracity_distortion, 6225-visual_veracity_distortion

### event_instance_visual_tie
Judge Fake when the image matches the claimed entity and event type but cannot be tied to the specific claimed event instance (e.g., year), and direct evidence shows multiple similar instances.
Triggers: image matches claimed entity and event type but lacks instance-specific identifiers (year, date, banners); direct evidence contains multiple similar event instances for the same entity
Steps: Identify the specific claimed event instance {claimed_instance} (entity, event type, year/date); Check whether {image_description} contains instance-specific identifiers; Check whether {direct_evidence_pool} lists multiple similar instances of the same event type; If the image lacks instance identifiers and multiple candidate instances exist, judge Fake
Conditions: image lacks year/date-specific cues; direct evidence lists multiple similar events for the same entity
Evidence Rules: direct evidence confirming the entity's participation in multiple similar events creates instance ambiguity, not confirmation of the claimed instance; irrelevant inverse evidence is non-contributing
Decision Criteria: image cannot be visually tied to the specific claimed instance -> Fake
Uncertainty: images with subtle year-specific cues not captured in the description
Support: 89803-fake
