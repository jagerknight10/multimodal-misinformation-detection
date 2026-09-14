# Unified multimodal misinformation verification skill

## Synthesized procedure

Multimodal misinformation verification: parse caption into claim elements; assess image-text consistency (inconclusive if identifiers or claim elements missing); filter evidence pools for relevance (irrelevant items non-contributing); cross-check image vs direct evidence and text vs inverse evidence; apply mismatch rules (entity/interaction visual tie, inverse-scene match, visual-attribute conflict); aggregate consistency findings into Real/Fake with cited rationale.

## Reusable workflows

### text_claim_analysis
Extract verifiable claim elements from the caption
Steps: Parse caption text; Identify entities, event, date, location, quantities; Formulate the claim to verify
Output Contract: structured claim summary
Supported by: 431849-real, 801666-real, 868253-real

### image_content_description
Produce a structured description of the image for comparison against the claim and evidence
Steps: Identify {image_subjects} and their visible actions; Describe {image_setting} and environment; Record presence/absence of each {claimed_element}; Note visual identifiers (species, landmarks, people, text)
Conditions: Image lacks visual identifiers -> mark low-identifiability
Output Contract: Structured description: subjects, setting, claimed-element presence/absence, identifiers
Supported by: 431849-real, 801666-real, 868253-real, 198663-fake, 1185433-real, 213108-real, 45926-real, 837138-real, 322977-fake, 199432-real, 597755-fake, 146372-fake, 410258-fake, 982456-real, 1236343-real, 298661-real, 582078-fake

### image_text_consistency_check
Determine whether the image content aligns with the claim elements.
Steps: Describe the image: people, actions, setting, and visual identifiers (signs, logos, venue).; Compare depicted entities, action, and setting against the claim elements.; Classify as consistent, inconsistent, or inconclusive.
Conditions: Caption too short or image lacks visual identifiers -> inconclusive.; Depicted interaction contradicts the claimed interaction -> inconsistent.; Claimed entity identifiable and setting broadly consistent but claimed action merely absent -> neutral/inconclusive.
Output Contract: Consistency label (consistent|inconsistent|inconclusive) with cited image details.
Supported by: 431849-real, 801666-real, 868253-real, 111829-real, 1488781-real, 1102464-real, 1589261-real, 198663-fake, 213108-real, 62591-real, 822340-real, 43627-real, 45926-real, 837138-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 597755-fake, 105708-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 1682986-fake, 637499-real, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 298661-real, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real

### evidence_consistency_check
Cross-check image vs direct evidence and text vs inverse evidence
Steps: If direct evidence present, compare image to it; If inverse evidence present, compare text to it; Note 'no evidence' for empty fields
Conditions: Skip check when corresponding evidence is empty
Output Contract: per-evidence verdict or 'no evidence'
Supported by: 431849-real, 801666-real, 868253-real

### final_judgement_aggregation
Aggregate consistency results into a final label
Steps: Summarize consistency findings; Weigh image-text and evidence results; Emit judgement
Conditions: Any contradiction supports Fake; all consistent supports Real
Output Contract: Judgement: Real|Fake
Supported by: 431849-real, 801666-real, 868253-real

### text_image_consistency_assessment
Determine whether the image matches the text description
Steps: Parse caption into claim elements (entities, events, locations, dates); Generate detailed visual description of the image; Compare image description against text claim elements for consistency
Conditions: Always executed
Output Contract: Consistent or Inconsistent with reasoning
Supported by: 424118-fake, 1003172-real, 187828-real

### evidence_cross_verification
Cross-check image and text against provided evidence
Steps: If direct evidence is present, check image consistency against it; If inverse evidence is present, check text consistency against it; Skip any evidence check if the evidence field is empty
Conditions: Skip direct evidence check if empty; Skip inverse evidence check if empty
Output Contract: Per-evidence consistency assessment or 'no evidence provided'
Supported by: 424118-fake, 1003172-real, 187828-real

### judgment_aggregation
Combine all consistency and evidence cross-check results into a final Real/Fake judgment
Steps: Review all consistency and evidence check results; Apply rules: inconclusive image-text consistency → rely on evidence cross-checks; partial entity mismatch with irrelevant inverse evidence → Fake; Determine final judgment: Real or Fake
Conditions: If image-text consistency is inconclusive, weight evidence cross-checks more heavily; If direct evidence has partial mismatch and inverse evidence is irrelevant, judge Fake; If all checks align, judge Real
Output Contract: Real or Fake judgment with aggregated reasoning
Supported by: 424118-fake, 1003172-real, 187828-real, 89803-fake, 460533-real

### Cross-modal verification pipeline
Determine Real/Fake by systematically comparing text claims against image content and available evidence.
Steps: Parse caption into claim elements (entity, action, setting, temporal); Produce detailed image description (objects, people, setting, edit cues); Assess image-text consistency (do visual elements support the text's claims); Cross-check image against direct evidence items (if any provided); Cross-check text against inverse evidence items (if any provided); Aggregate all consistency signals into a Real/Fake judgement with step-by-step reasoning
Conditions: Skip direct-evidence step when no direct evidence is supplied; Skip inverse-evidence step when no inverse evidence is supplied; If inverse evidence aligns with the image's generic setting but not the text's specific entity claim, treat as a signal that the text's specific claims are unsupported
Output Contract: Ordered step-by-step analysis followed by a final Real/Fake judgement
Supported by: 6133-visual_veracity_distortion, 6225-visual_veracity_distortion, 693635-fake

### cross_modal_verification_pipeline
Judge whether a news image is used correctly in its caption context (Real/Fake) by combining image-text consistency with evidence cross-checks.
Steps: Parse the caption into claim elements (entities, action, setting, purpose).; Describe the image in detail and assess image-text consistency; mark inconclusive if the caption is too short or the image lacks visual identifiers.; Cross-check the image against each direct evidence item, skipping empty or irrelevant items.; Cross-check the text against each inverse evidence item, skipping empty or irrelevant items.; Aggregate consistency and evidence results into a Real/Fake judgement with per-step reasoning.
Conditions: If image-text consistency is inconclusive, rely on evidence cross-checks for the judgement.; If the image depicts a different or contradictory interaction than the claimed one, judge Fake even when direct evidence confirms the event.; If the image is neutral (claimed entity identifiable, setting broadly consistent, claimed action merely absent), rely on evidence cross-checks and judge Real when direct evidence confirms the event and inverse evidence has no contradictions.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.; Irrelevant or off-topic evidence items are treated as non-contributing, not as contradictions.
Output Contract: Real/Fake judgement with step-by-step reasoning covering text analysis, image description, consistency, and both evidence cross-checks.
Supported by: 514577-real, 272289-real, 206694-real, 146372-real, 246181-real, 940097-real, 50978-fake, 404887-fake, 300990-real, 208379-real

### claim_and_image_grounding
Establish claim elements and visual grounding before evidence checks.
Steps: Parse the caption into claim elements: entities, event, location, date.; Describe the image in detail, noting visual identifiers (architecture, people, objects).; Compare the image description with the claim elements and record consistency.
Conditions: Caption too short or image lacks visual identifiers -> mark image-text consistency inconclusive.
Output Contract: Claim element list, image description, image-text consistency status (consistent / inconsistent / inconclusive).
Supported by: 111829-real, 1488781-real, 307680-fake, 545751-real, 205992-fake

### evidence_cross_check
Cross-check the image against direct evidence and the text against inverse evidence.
Steps: For each direct evidence item, assess relevance to the image (event, venue, entities).; For each inverse evidence item, assess relevance to the text and whether it contradicts or corroborates the claim.; Skip empty or off-topic items as non-contributing.; Record per item: contradiction, corroboration, or partial entity mismatch.
Conditions: Item empty or off-topic -> non-contributing, not a contradiction.; Inverse item corroborates the claim -> non-contradictory.; Image setting or visual details match an inverse-evidence scene -> item is image-relevant.
Output Contract: Per-item flags: relevant|non_contributing and corroborates|contradicts|partial_mismatch.
Supported by: 111829-real, 1488781-real, 1102464-real, 1589261-real, 198663-fake, 400247-fake, 1185433-real, 213108-real, 822340-real, 43627-real, 45926-real, 837138-real, 99167-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 98106-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 272321-fake, 1682986-fake, 1682986-real, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 205992-fake, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 1117352-real, 298661-real, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real

### judgement_aggregation
Aggregate consistency and evidence results into a final Real/Fake judgement.
Steps: Apply hard overrides: contradictory depicted interaction, or image matching an inverse-evidence scene -> Fake.; If image-text consistency is inconclusive, rely on evidence cross-checks.; If direct evidence confirms the event and inverse evidence has no contradictions -> Real.; Emit the final Real/Fake judgement with the deciding factors.
Conditions: Partial entity mismatch in direct evidence with aligned context and clean inverse evidence -> does not override Real.; No hard override and evidence aligned -> Real.
Output Contract: Final label Real|Fake plus the deciding evidence factors.
Supported by: 111829-real, 1488781-real, 1102464-real, 1080184-fake, 1589261-real, 198663-fake, 400247-fake, 1185433-real, 450468-fake, 198663-real, 213108-real, 62591-real, 822340-real, 43627-real, 45926-real, 837138-real, 99167-real, 283101-real, 322977-fake, 1119341-real, 199432-real, 597755-fake, 98106-real, 105708-real, 98106-fake, 143664-real, 146372-fake, 1221030-real, 307680-fake, 545751-real, 272321-fake, 1682986-fake, 637499-real, 1682986-real, 576980-fake, 410258-fake, 982456-real, 1236343-real, 199961-fake, 47981-real, 205992-fake, 595563-real, 125127-fake, 791248-fake, 139570-fake, 816513-real, 1117352-real, 298661-real, 885904-fake, 1553640-real, 917151-real, 235782-fake, 451561-fake, 462287-real, 582078-fake, 179993-real

### Cross-modal misinformation verification pipeline
Determine whether a caption-image pair contains cross-modal misinformation by grounding the claim in the image and cross-checking both against provided evidence.
Steps: Parse the caption into claim elements (people, work, event, date, setting).; Describe the image's scene, attire, setting, and any identifiable entities.; Assess image-text consistency against the claim elements.; Cross-check the image against direct evidence and the text against inverse evidence, skipping empty evidence.; Aggregate the consistency signals into a Real/Fake judgement with a stated reason.
Conditions: Skip an evidence cross-check when the corresponding evidence is empty.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.; If inverse evidence attributes the image to a different source than the caption claims, treat it as a source mismatch.
Output Contract: A Real/Fake judgement with a brief justification citing the decisive consistency signal.
Supported by: 410430-fake

### claim_decomposition
Parse the caption into verifiable claim elements before any cross-modal comparison.
Steps: Extract named entities (people, organizations) from the caption.; Extract the claimed event, setting, and action/interaction if present.; Flag elements too short or vague to verify visually.
Conditions: Caption lacks explicit event or action -> mark those elements unverifiable from text alone.
Output Contract: Structured claim elements: entities[], event, setting, action, verifiability flags.
Supported by: 1102464-real, 62591-real, 98106-real, 1221030-real, 272321-fake, 199961-fake, 595563-real, 791248-fake, 139570-fake, 235782-fake, 179993-real

### claim_element_parsing
Decompose the caption into atomic, verifiable claim elements
Steps: Read the caption text; Extract {claimed_subject}, {claimed_action}, {claimed_setting}, {claimed_location}; Flag the caption as low-information if it lacks verifiable identifiers
Conditions: Caption too short or missing identifiers -> mark low-information for downstream consistency check
Output Contract: Structured claim elements: subject, action, setting, location
Supported by: 1080184-fake, 1589261-real, 198663-fake, 198663-real, 45926-real, 199432-real, 143664-real, 146372-fake, 410258-fake, 982456-real, 47981-real, 462287-real, 582078-fake

### image_scene_description
Produce a detailed structured description of the image for comparison.
Steps: Identify main subjects and objects {subjects, objects}.; Identify setting/venue cues {venue_cues}.; Identify weather and lighting {weather, lighting}.; Identify contextual props (tents, crowds, signage) {context_cues}.
Conditions: Image is present
Output Contract: structured {image_description}
Supported by: 1080184-fake, 1682986-fake

### cross_modal_consistency_check
Verify consistency between image, caption, and evidence
Steps: Compare image description against claim elements; Compare image against direct evidence captions; Compare caption against inverse evidence items
Conditions: Skip direct-evidence check if direct evidence is empty; Skip inverse-evidence check if inverse evidence is empty
Output Contract: Per-check consistency verdict (consistent / inconsistent / not checked)
Supported by: 1080184-fake, 1185433-real, 450468-fake, 198663-real

### evidence_context_matching
Cross-check image and text against the supplied evidence
Steps: If direct evidence is non-empty, compare the image against direct-evidence descriptions; If inverse evidence is non-empty, compare the text and image cues against inverse-evidence context; Skip any empty evidence set
Conditions: Direct or inverse evidence is non-empty
Output Contract: Per-evidence consistency signals
Supported by: 1080184-fake

### cross_modal_claim_verification
Judge whether a news image matches its caption by combining image-text consistency with direct and inverse evidence cross-checks.
Steps: Parse the caption into claim elements: actors, event, setting, and date.; Describe the image and identify visible entities, activity, and setting.; Compare image entities and setting against the caption's claim elements for consistency.; Cross-check the image against direct evidence and the caption against inverse evidence, skipping any empty evidence set.; Aggregate all consistency results into a Real/Fake judgement with a rationale.
Conditions: If image entities or event contradict the caption's claim, flag the image as out of context.; Skip the direct-evidence or inverse-evidence check when that evidence set is empty.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.
Output Contract: Real/Fake judgement with step-by-step rationale covering image-text consistency, direct-evidence check, and inverse-evidence check.
Supported by: 127382-fake

### cross_modal_verification
Verify whether a news image is consistent with its caption and supporting evidence, producing a Real/Fake judgement.
Steps: Parse the caption into claim elements {claim_elements} (entities, locations, events).; Describe the image content to produce {image_description}.; Check consistency between {image_description} and {claim_elements}.; Cross-check the image against {direct_evidence} and the text against {inverse_evidence}, skipping empty evidence.; Aggregate all consistency results into a {judgment} of Real or Fake.
Conditions: Skip a direct/inverse evidence check if that evidence is empty.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.
Output Contract: A Real/Fake judgement with supporting reasoning.
Supported by: 1592209-fake

### parse_claim_elements
Decompose the news caption into verifiable claim elements
Steps: Read the caption text; Identify the named subject (person or organization); Extract the asserted statement or quote; Extract context elements (event, time, location)
Conditions: Skip elements not present in the caption
Output Contract: Structured claim elements: subject, statement, context
Supported by: 134721-fake

### describe_image
Produce a factual description of the image independent of the caption
Steps: Identify the main subject/person; Describe the setting and backdrop; Transcribe visible text; Note distinguishing features (e.g., hair, clothing)
Conditions: Image unreadable or missing -> mark description unavailable
Output Contract: Free-text image description with subject, setting, visible text
Supported by: 134721-fake, 735459-real

### check_image_text_consistency
Determine whether the image supports, contradicts, or is inconclusive against the caption's claim elements.
Steps: Map image elements to each claim element; Assess alignment of people, event, location, and context; Classify as consistent, inconsistent, or inconclusive
Conditions: Caption too short or image ambiguous -> inconclusive; Partial entity mismatch -> note, do not override overall context alignment
Output Contract: {consistency: consistent|inconsistent|inconclusive, notes}
Supported by: 134721-fake, 99203-real, 735459-real, 1248657-real

### cross_check_evidence
Verify the image against direct evidence and the text against inverse evidence, ignoring non-contributing items.
Steps: For each {direct_evidence_item}, check image context alignment; For each {inverse_evidence_item}, check text context alignment; Skip empty or off-topic items as non-contributing
Conditions: Irrelevant item -> non-contributing, not a contradiction; Partial entity mismatch in direct evidence with overall context aligned -> does not override
Output Contract: {direct_alignment, inverse_alignment, contributing_items}
Supported by: 134721-fake, 99203-real, 735459-real, 1248657-real

### aggregate_judgment
Combine consistency and evidence signals into a final verdict
Steps: Weigh the image-text consistency result; Weigh the direct and inverse evidence verdicts; Apply the partial-mismatch rule: a different person at the same venue does not override context alignment when inverse evidence supports the text setting; Issue a Real or Fake judgement with rationale
Conditions: Fake if the image depicts an unrelated subject or evidence contradicts the claim; Real if image, text, and evidence align
Output Contract: Real/Fake judgement with a short rationale
Supported by: 134721-fake

### claim_image_alignment
Determine whether the image depicts the event asserted by the caption
Steps: Parse caption into claim elements (person, action, object, date, location); Describe image content (people, actions, setting, era cues); Compare image description against each claim element; Flag mismatched elements (person, date, event)
Conditions: Mark image-text inconsistent if any core claim element contradicts the image
Output Contract: Consistency verdict plus list of mismatched claim elements
Supported by: 400247-fake

### Cross-modal claim-image verification
Decide whether a news image is faithful to its caption by cross-checking both against direct and inverse evidence.
Steps: Parse the caption into claim elements (actors, action, location, event, time).; Describe the image content in detail.; Assess image-text consistency against the claim elements.; Cross-check the image against direct evidence and the text against inverse evidence, skipping any empty evidence.; Aggregate the consistency signals into a Real/Fake judgement with a brief justification.
Conditions: If the image and text describe different events, judge Fake.; Skip empty direct or inverse evidence rather than treating absence as a signal.; A partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting.
Output Contract: A Real/Fake judgement plus a short justification citing which evidence supported the image vs the text.
Supported by: 113060-fake

### parse_caption_claims
Decompose the caption into verifiable claim elements
Steps: Read the caption; Identify the subject person/entity; Identify the asserted statement or relationship; List claim elements for later checks
Conditions: Caption empty or too short to verify -> mark claim as unverifiable
Output Contract: Structured claim elements: subject, statement, entities
Supported by: 99203-real, 735459-real

### describe_news_image
Produce a factual image description independent of the caption.
Steps: Identify the main subject and apparent role; Describe the setting and activity; Note salient objects (flags, podium, signage)
Conditions: Describe only visible content; do not infer identity from the caption
Output Contract: Free-text description with subject, setting, and objects
Supported by: 99203-real

### aggregate_real_fake_judgement
Combine all consistency checks into a final verdict.
Steps: Collect verdicts from image-text, direct-evidence, and inverse-evidence checks; Weigh contradictions against supporting context; Emit the final Real/Fake judgement with brief rationale
Conditions: No contradiction and aligned context -> Real; A specific claim element contradicted by evidence -> Fake
Output Contract: Judgement: Real|Fake with concise rationale
Supported by: 99203-real

### claim_element_extraction
Decompose the caption into discrete verifiable claim elements.
Steps: Identify claimed entities, locations, events, actions, and time references in the caption; Record each element as a separate checkable fact
Conditions: If the caption is too short to yield checkable elements, flag the claim as under-specified
Output Contract: List of claim elements (entity, location, event, action, time)
Supported by: 1185433-real, 43627-real, 837138-real, 816513-real

### claim_and_image_analysis
Produce structured inputs for cross-modal comparison by extracting claim elements and describing the image.
Steps: Parse the caption into claim elements (location, entity, setting, date).; Describe the image in detail (content, perspective, key visual features).
Output Contract: Structured claim elements plus a detailed image description.
Supported by: 450468-fake

### image_description
Produce a factual image description usable for comparison
Steps: Identify visible {entities} and their {actions}; Describe {setting} and visual identifiers (flags, venue, objects); Note identifiers that could anchor or contradict the claim
Conditions: Image lacks visual identifiers -> flag for inconclusive consistency
Output Contract: Structured description: entities, actions, setting, identifiers
Supported by: 198663-real, 143664-real, 1221030-real, 272321-fake, 1682986-real, 199961-fake, 47981-real, 139570-fake, 816513-real, 1117352-real, 235782-fake, 462287-real

### caption_claim_decomposition
Decompose the caption into verifiable claim elements
Steps: Extract entities and actions from the caption; Extract location and time references; List claim elements for downstream checks
Conditions: If the caption is too short to verify, mark it inconclusive
Output Contract: List of claim elements {entities, actions, location, time}
Supported by: 213108-real, 597755-fake, 1236343-real

### dual_evidence_cross_check
Cross-check image against direct evidence and text against inverse evidence
Steps: Scan direct evidence for items matching the image subject and setting; Record partial mismatches (same venue/actor, different entity) without immediate rejection; Scan inverse evidence for items matching the text claim elements; Skip empty or irrelevant evidence items
Conditions: If direct evidence shows a partial entity mismatch, defer to inverse-evidence support before rejecting
Output Contract: Per-evidence match/mismatch notes citing the specific matched or conflicting items
Supported by: 62591-real

### claim_element_decomposition
Parse the caption into discrete verifiable claim elements
Steps: Extract {actor}, {action}, {target}, {location}, {date} from {caption}; Record each element as a discrete claim for downstream verification
Conditions: If {caption} is too short to yield discrete elements, mark the claim as under-specified
Output Contract: List of claim elements {actor, action, target, location, date}
Supported by: 822340-real, 322977-fake, 98106-fake, 1682986-fake, 298661-real

### claim_parse_image_describe
Establish claim elements from the caption and visual facts from the image for downstream consistency checks.
Steps: parse caption into claim elements (person, age, location, event); describe image (people, clothing, setting, actions); record both for consistency checks
Conditions: caption may be short or incomplete; image may be ambiguous
Output Contract: list of claim elements + image description
Supported by: 99167-real

### image_text_consistency
Determine whether the image supports, contradicts, or is inconclusive for the claim
Steps: Compare claim elements against image description; Classify as consistent, contradictory, or inconclusive; If contradictory interaction, mark Fake-leaning; if neutral, defer to evidence
Conditions: Caption too short or image lacks identifiers -> inconclusive; Contradictory interaction -> Fake even if direct evidence confirms; Neutral image -> rely on evidence cross-checks
Output Contract: Consistency label (consistent/contradictory/inconclusive) with rationale
Supported by: 99167-real, 98106-real, 272321-fake, 1682986-real, 1117352-real

### claim_parse_and_image_describe
Establish claim elements and visual facts for comparison
Steps: Parse caption into claim elements: entities, relationships, actions, setting; Describe image in detail: people, actions, setting, visual identifiers
Conditions: If caption too short or image lacks visual identifiers, flag for inconclusive handling
Output Contract: Structured claim elements plus detailed image description
Supported by: 283101-real, 917151-real

### bidirectional_evidence_cross_check
Verify the image against direct evidence and the text against inverse evidence
Steps: For each direct evidence item, check whether the image matches the described entity/setting/event; For each inverse evidence item, check whether the text claim is contradicted; Skip empty or off-topic items and mark them non-contributing; Record matches, mismatches, and non-contributing items
Conditions: Partial entity mismatch (different person at same venue) does not override overall context alignment; Off-topic items are non-contributing, not contradictions
Output Contract: Per-evidence-item match/mismatch/non-contributing summary
Supported by: 597755-fake, 105708-real, 637499-real, 885904-fake

### image_description_with_location_cues
Describe the image and resolve its actual location from visible cues
Steps: Identify main subjects and their apparent group or role; Extract visible location indicators (signs, landmarks, in-scene text); Infer the actual location from the cues
Conditions: If no location cues are visible, record location as undetermined
Output Contract: Image description: subjects, group/role, location cues, inferred location
Supported by: 98106-fake

### claim_image_grounding
Extract claim elements from the caption and describe the image to establish comparable facts before consistency checks
Steps: Parse the caption into claim elements (subject, role, event, time, location); Describe the image (subject, action, setting, context)
Conditions: Caption too short to verify -> mark image-text consistency as inconclusive
Output Contract: Structured claim elements + image description
Supported by: 164672-fake

### consistency_evidence_judgement
Determine image-text consistency, cross-check against direct and inverse evidence, and aggregate into a Real/Fake judgment
Steps: Compare image description with caption claims -> consistent/inconsistent/inconclusive; Cross-check image against direct evidence (skip if empty); Cross-check text against inverse evidence (skip if empty); Aggregate all signals into a Real/Fake judgment
Conditions: Image-text inconclusive -> rely on evidence cross-checks; Partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting
Output Contract: Real/Fake judgment with reasoning
Supported by: 164672-fake

### aggregate_judgement
Combine consistency signals into a final Real/Fake judgement.
Steps: Weigh image-text consistency, direct-evidence alignment, and inverse-evidence alignment; If image-text is inconclusive, rely on evidence cross-checks; Emit Real/Fake with a brief rationale
Conditions: All contributing sources aligned -> Real; Material contradiction in contributing evidence -> Fake
Output Contract: {judgement: Real|Fake, rationale}
Supported by: 735459-real, 1248657-real

### claim_decomposition_and_image_description
Extract structured claim elements from text and generate a detailed image description for downstream checks
Steps: Parse text into claim elements: person, event, date, location, action; Describe image in detail: subject, setting, objects, context, visual cues
Conditions: Always executed as first step
Output Contract: Structured claim elements + free-text image description
Supported by: 89803-fake, 460533-real

### image_text_consistency_assessment
Determine whether the image supports, contradicts, or is inconclusive for the caption claim
Steps: Parse the caption into claim elements (entity, action, event, location, date); Describe the image's visible content (people, setting, objects, actions); Compare image content against the claim elements; Classify as consistent, inconsistent, or inconclusive
Conditions: Caption too short or image lacks visual identifiers -> inconclusive; Image depicts a different or contradictory interaction -> inconsistent
Output Contract: Consistency label (consistent/inconsistent/inconclusive) with rationale
Supported by: 89803-fake, 460533-real, 885904-fake

### direct_evidence_image_cross_check
Verify the image against direct evidence items
Steps: Enumerate direct evidence items; Skip empty or irrelevant items; Compare image entities and setting against evidence; Note when evidence supports the claim but lacks visual detail
Conditions: Empty or irrelevant evidence items are skipped
Output Contract: support status: supports | contradicts | no visual detail
Supported by: 89803-fake, 460533-real, 576980-fake

### inverse_evidence_text_cross_check
Check the text against inverse evidence for contradictions
Steps: Enumerate inverse evidence items; Treat off-topic items as non-contributing; Compare claim setting against inverse evidence contexts; Flag contradiction only on direct conflict with the claim
Conditions: Off-topic items are non-contributing, not contradictions
Output Contract: contradiction status: contradicts | no contradiction
Supported by: 89803-fake, 460533-real, 576980-fake

### claim_parsing
Decompose the caption into verifiable claim elements
Steps: Read the caption; Identify entities, actions, setting, and time elements; List claim elements for downstream checks
Conditions: Caption too short -> flag low-information for consistency check
Output Contract: Structured claim elements (entity, action, setting, time)
Supported by: 1682986-real, 1117352-real

### claim_decomposition_and_image_text_consistency
Determine whether the image supports the caption's claim elements
Steps: Parse the caption into claim elements (entities, action, location, time/event); Describe the image content in detail; Compare image content against each claim element; Mark inconclusive if the image does not clearly indicate the claimed location or event
Conditions: Image ambiguous about location/event -> inconclusive, not inconsistent
Output Contract: consistency status: consistent | inconsistent | inconclusive
Supported by: 576980-fake

### parse_claim_and_describe_image
Decompose the caption into verifiable claim elements and produce a detailed image description as the basis for all consistency checks.
Steps: Extract claim elements from the caption: {people}, {event}, {location}, {context}; Describe the image: subjects, objects, setting, activity, and salient details
Conditions: Caption too short to yield verifiable elements -> flag for inconclusive consistency
Output Contract: {claim_elements, image_description}
Supported by: 1248657-real

### claim_and_image_decomposition
Establish claim elements and observable image content for comparison.
Steps: parse caption into claim elements (entities, action/interaction, setting, time); describe the image in detail (visible entities, actions, objects, setting cues); flag claim elements lacking visual identifiers in the image
Conditions: caption too short or image lacks visual identifiers -> mark consistency inconclusive
Output Contract: structured claim elements plus detailed image description
Supported by: 125127-fake

### evidence_relevance_filtering
Classify and filter direct/inverse evidence items before cross-checking so off-topic items do not skew the judgement.
Steps: Classify each evidence item as relevant or irrelevant to the claim; Skip irrelevant/off-topic items (treat as non-contributing, not contradictions); Retain only relevant items for the image and text cross-checks
Conditions: evidence item off-topic or unrelated -> skip; evidence item relevant -> use for cross-check
Output Contract: Filtered set of relevant evidence items
Supported by: 300990-real

### claim_parsing_and_image_description
Extract claim elements from the caption and produce a factual image description as the basis for consistency checking
Steps: Parse the caption into claim elements (actors, entities, actions, setting); Describe the image: visible entities, attire, objects, setting, actions
Conditions: Caption too short or image lacks visual identifiers -> mark downstream consistency inconclusive
Output Contract: claim_elements + image_description
Supported by: 1553640-real

### cross_modal_misinformation_verification
Determine whether a news image supports or contradicts its caption's claim by combining image-text consistency with evidence cross-checks
Steps: Parse the caption into claim elements (entities, roles, expected event); Describe the image in detail (people, setting, actions, visual identifiers); Check image-text consistency; mark inconclusive if the caption is too short or the image lacks visual identifiers; Cross-check the image against direct evidence and the text against inverse evidence, skipping empty or irrelevant items; Aggregate the consistency results into a Real/Fake judgement
Conditions: If the image depicts a different or contradictory interaction than the claimed one, judge Fake even if direct evidence confirms the event; If the image is neutral (claimed entity identifiable, setting broadly consistent, claimed action absent but not contradicted), rely on evidence cross-checks; If the image aligns with the inverse-evidence context, treat it as corroboration of the image-text mismatch
Output Contract: Real/Fake judgement with per-check reasoning
Supported by: 1505500-fake

### claim_and_image_parsing
Extract verifiable elements from the caption and a detailed description of the image.
Steps: parse caption into claim_elements (actors, action, location, time); describe image: people, objects, setting, activity, atmosphere
Output Contract: claim_elements list plus structured image_description
Supported by: 451561-fake

## Evidence and decision rules

### image_text_consistency_check
Purpose: Determine whether the image faithfully depicts the claim in the caption
Triggers: caption text and image both present
Inputs: text claim summary; image description
Steps: Compare depicted entities, setting, and attributes against claim elements; Record consistency verdict with rationale
Conditions: Flag inconsistent if visual elements contradict the claim
Evidence Rules: Use only observed visual elements and stated claim elements; no external knowledge
Decision Criteria: All key claim elements plausibly represented in image
Output Contract: consistent|inconsistent with justification
Uncertainty: Ambiguous or low-detail images where claim elements cannot be confirmed or refuted
Supported by: 431849-real, 801666-real, 868253-real

### evidence_consistency_check
Purpose: Cross-check image against direct evidence and text against inverse evidence
Triggers: direct or inverse evidence field non-empty
Inputs: image description; direct evidence; text claim; inverse evidence
Steps: If direct evidence present, compare image to it; If inverse evidence present, compare text to it; Note 'no evidence' when a field is empty
Conditions: Skip direct-evidence check when empty; Skip inverse-evidence check when empty
Evidence Rules: Treat evidence entries as reference items only; do not assume unprovided content
Decision Criteria: No contradiction between image and direct evidence, or text and inverse evidence
Output Contract: per-evidence verdict or 'no evidence' note
Uncertainty: Evidence sources that are non-visual or unverifiable from the image
Supported by: 431849-real, 801666-real, 868253-real

### final_judgement_aggregation
Purpose: Aggregate consistency findings into a final label
Triggers: all consistency checks complete
Inputs: image-text verdict; evidence verdicts
Steps: Summarize prior consistency findings; Emit final judgement label
Conditions: Contradiction in any check supports Fake; all consistent supports Real
Evidence Rules: Judgement must cite the consistency results, not external facts
Decision Criteria: Overall alignment of image, text, and available evidence
Output Contract: Judgement: Real|Fake
Uncertainty: Mixed or inconclusive consistency signals
Supported by: 431849-real, 801666-real, 868253-real

### rule_from_431849-real
Purpose: Dataset-supported verification rule
Steps: Skip evidence checks when the corresponding evidence field is empty and base the judgement on image-text consistency
Supported by: 431849-real

### rule_from_801666-real
Purpose: Dataset-supported verification rule
Steps: When evidence is present, compare image to direct evidence and text to inverse evidence before concluding
Supported by: 801666-real

### rule_from_868253-real
Purpose: Dataset-supported verification rule
Steps: Match claim attributes such as dates and object types against observed visual attributes in the consistency check
Supported by: 868253-real

### partial_mismatch_aggregation
Purpose: Handle partial entity mismatches in direct evidence during judgment aggregation
Triggers: direct evidence names a different entity than the text but shares venue or event context
Inputs: direct_evidence; text_claims; inverse_evidence
Steps: Identify the mismatched entity in direct evidence; Verify shared context (venue, event type) still aligns; Check whether inverse evidence supports the text setting; If no definitive contradiction and overall context aligns, judge Real
Conditions: direct evidence has entity mismatch but shared context; inverse evidence supports text setting
Evidence Rules: Partial entity mismatch in direct evidence is not a definitive contradiction when venue and event context align
Decision Criteria: No definitive contradictory information; Strong alignment in setting and style; Inverse evidence supports the text theme
Output Contract: Real/Fake judgement with reasoning
Uncertainty: Whether venue-level match with person-level mismatch is always sufficient for Real
Supported by: 187828-real

### rule_from_187828-real
Purpose: Dataset-supported verification rule
Steps: Partial entity mismatch in direct evidence does not override overall context alignment when inverse evidence supports the text setting
Supported by: 187828-real

### short_caption_inconclusive
Purpose: Handle captions too short to independently verify image-text consistency.
Triggers: caption lacks sufficient claim elements (e.g., only name/age)
Inputs: caption; image description
Steps: parse caption into claim elements; assess whether claim elements are sufficient for image-text comparison; if insufficient, mark image-text consistency as inconclusive; defer judgement to evidence cross-checks
Conditions: caption too short → inconclusive; caption sufficient → proceed with comparison
Evidence Rules: when image-text is inconclusive, rely on image-direct and text-inverse evidence alignment
Decision Criteria: sufficient claim elements for comparison
Output Contract: image-text consistency verdict (match/mismatch/inconclusive)
Uncertainty: threshold for 'too short' is not precisely defined
Supported by: 99167-real

### rule_from_99167-real
Purpose: Dataset-supported verification rule
Steps: When the caption lacks sufficient claim elements for image-text comparison, mark that check as inconclusive and rely on image-direct and text-inverse evidence alignment for the judgement.
Supported by: 99167-real

### evidence_relevance_filter
Purpose: Prevent off-topic evidence items from distorting cross-checks
Triggers: evidence pool contains items unrelated to the claim's entities, events, or setting
Inputs: direct evidence list; inverse evidence list; claim elements
Steps: Extract claim elements (entities, events, dates, locations); Filter each evidence item for relevance to claim elements; Treat irrelevant items as non-contributing (neither supporting nor contradicting); Cross-check only relevant items against the image (direct) or text (inverse)
Conditions: If all items in a pool are irrelevant, record the pool as non-contributing and continue
Evidence Rules: Irrelevant evidence is neither supporting nor contradicting; Relevant direct evidence is matched against image content; relevant inverse evidence against text claim elements
Decision Criteria: A pool contributes only if at least one item is relevant to the claim
Output Contract: Per-pool relevance note plus support/contradiction/neutral status
Uncertainty: Relevance of ambiguous items (e.g., generic terms) is judged by co-occurrence with claim-specific entities
Supported by: 1682986-real

### rule_from_1682986-real
Purpose: Dataset-supported verification rule
Steps: Skip empty or irrelevant evidence items during cross-checks; irrelevant items are neither supporting nor contradicting
Supported by: 1682986-real

### unconfirmed_entity_image_fake
Purpose: Resolve inconclusive image-text consistency when direct evidence confirms only the setting, not the claimed entities
Triggers: image-text consistency inconclusive due to missing visual identifiers; direct evidence supports setting but lacks entity confirmation
Inputs: caption claim elements; image description; direct evidence items; inverse evidence items
Steps: mark image-text consistency inconclusive when the image lacks identifiers for claimed persons or location; check whether direct evidence confirms setting and/or entities; treat irrelevant inverse evidence as non-contributing; judge Fake if the image cannot be visually tied to the claimed entities despite setting support
Conditions: direct evidence confirms setting but not entities; inverse evidence irrelevant
Evidence Rules: setting-only support from direct evidence is a weak positive, not entity confirmation; irrelevant inverse evidence is non-contributing, not contradicting
Decision Criteria: absence of visual confirmation of claimed entities in the image yields Fake when consistency is inconclusive
Output Contract: Real/Fake judgement with rationale citing consistency status and evidence contributions
Uncertainty: cases where direct evidence visually confirms entities but consistency is inconclusive for other reasons
Supported by: 199961-fake

### rule_from_199961-fake
Purpose: Dataset-supported verification rule
Steps: When image-text consistency is inconclusive and direct evidence confirms the setting but not the specific claimed entities, judge Fake because the image cannot be tied to the claim.
Supported by: 199961-fake

### specific_interaction_visual_tie
Purpose: Extend the Fake-judgement visual-tie rule from entity-level to interaction-level: the image must depict the specific claimed action/object, not merely the claimed entity and setting.
Triggers: image shows the claimed entity and setting but not the specific claimed interaction
Inputs: image description; claim elements; direct evidence
Steps: identify the specific claimed interaction/object; check whether the image depicts it; if absent, mark the image as wrongly used for the more specific context
Conditions: entity and setting match but claimed interaction absent -> Fake; direct evidence confirms the event occurred but the image does not depict it -> still Fake
Evidence Rules: direct evidence confirming event occurrence does not rescue an image that omits the claimed interaction
Decision Criteria: image must depict the specific claimed interaction, not just the entity/setting
Output Contract: Fake judgement with rationale that the image is wrongly used for this news context
Uncertainty: interaction plausible but not visible due to framing or cropping
Supported by: 125127-fake

### rule_from_125127-fake
Purpose: Dataset-supported verification rule
Steps: If the image cannot be visually tied to the specific claimed interaction (entity/setting match but claimed action/object not depicted), judge Fake even when direct evidence confirms the event occurred.
Supported by: 125127-fake

### neutral_image_action_absence
Purpose: Distinguish a neutral image (claimed entity identifiable, claimed action merely absent) from a contradictory image (different interaction depicted), so the Fake override applies only to the latter.
Triggers: image shows the claimed entity but not the claimed action; image is neutral/ambiguous (entity present, action absent but not contradicted)
Inputs: image; caption; direct evidence; inverse evidence
Steps: Identify whether the image depicts the claimed entity; Determine whether the image depicts the claimed action, a different/contradictory interaction, or neither (neutral); If neutral, rely on evidence cross-checks for the judgement; If a different/contradictory interaction is depicted, judge Fake; Aggregate into Real/Fake
Conditions: image depicts a different/contradictory interaction -> Fake; image neutral (entity identifiable, action absent but not contradicted) -> rely on evidence cross-checks
Evidence Rules: direct evidence confirming the event supports Real when the image is neutral; irrelevant/off-topic evidence items are non-contributing, not contradictions
Decision Criteria: entity identifiable + setting broadly consistent + no contradicting evidence -> Real (neutral image); different/contradictory interaction depicted -> Fake
Output Contract: Real/Fake judgement with reasoning
Uncertainty: Partially contradictory images (some elements match, some conflict) remain unresolved.
Supported by: 300990-real

### rule_from_300990-real
Purpose: Dataset-supported verification rule
Steps: If the image depicts a different or contradictory interaction than the claimed one, judge Fake even when direct evidence confirms the event; if the image is neutral (claimed entity identifiable, setting broadly consistent, claimed action merely absent and not contradicted), rely on evidence cross-checks and judge Real when direct evidence confirms the event and inverse evidence has no contradictions.
Supported by: 300990-real

### inverse_scene_match_override
Purpose: Judge Fake when the image's setting or visual details positively match an inverse-evidence scene (different location/event), even if direct evidence supports the text.
Triggers: image visual details align with an inverse-evidence scene; direct evidence supports the text but not the image's visual details
Inputs: image_description; inverse_evidence_items; direct_evidence_items; claim_elements
Steps: compare image setting, objects, and people against inverse-evidence scenes; verify direct evidence does not describe the image's distinctive visual details; flag image-source mismatch; judge Fake with rationale citing the inverse-scene match
Conditions: inverse evidence is on-topic and matches the image (not irrelevant); claimed action may be present (e.g., fire) while the setting differs
Evidence Rules: inverse evidence matching the image is image-relevant, not non-contributing; direct evidence supporting the text does not override an image-source mismatch
Decision Criteria: image matches the inverse scene better than the claimed scene -> Fake
Output Contract: Fake judgement with rationale naming the matched inverse scene and the unmatched claimed setting
Uncertainty: image partially matches both the claimed and an inverse scene
Supported by: 451561-fake

### rule_from_451561-fake
Purpose: Dataset-supported verification rule
Steps: When the image's setting or visual details positively match an inverse-evidence scene, judge Fake even if direct evidence supports the text.
Supported by: 451561-fake

### visual_attribute_conflict_fake
Purpose: Judge Fake when the image lacks identifiers for the claimed entity and its observable visual attributes conflict with the entity's known visual attributes
Triggers: image lacks visual identifiers for the claimed person/entity; image visual attributes conflict with the claimed entity's known visual attributes
Inputs: image description; caption claim elements; direct evidence
Steps: Identify the claimed entity and its known visual attributes; Check whether the image depicts identifiers for the claimed entity; Compare image visual attributes (e.g., clothing color, objects) against the claimed entity's known attributes; If no identifiers and attributes conflict, judge Fake
Conditions: no visual identifiers for the claimed entity; visual attribute conflict present
Evidence Rules: direct evidence showing the entity in different visual contexts reinforces the mismatch; irrelevant evidence items are non-contributing
Decision Criteria: image cannot be tied to the claimed entity and its visual attributes conflict with the claim
Output Contract: Fake judgement with rationale citing the visual attribute conflict
Uncertainty: known visual attributes rely on common knowledge about the entity; attribute conflicts may be coincidental (e.g., generic clothing colors)
Supported by: 349545-fake

### rule_from_349545-fake
Purpose: Dataset-supported verification rule
Steps: When the image lacks identifiers for the claimed entity and its observable visual attributes conflict with the entity's known visual attributes, judge Fake.
Supported by: 349545-fake
