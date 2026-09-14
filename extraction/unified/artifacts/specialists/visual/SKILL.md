# Check_visual_manipulation

## Scope

Assess visual veracity, medium, and manipulation using only the supplied task inputs and evidence.

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

### image_manipulation_screening
Detect manipulation artifacts and AI generation in the image
Steps: Examine {image} for face swap, facial expression alteration, or Photoshop edits; Determine if {image} is AI-generated or a real photo; Record {manipulation_finding} and {ai_generated}
Conditions: artifacts present -> manipulated; no artifacts + real photo -> original
Output: {manipulation_finding}: {manipulated, original}; {ai_generated}: {yes, no}; manipulation_type if manipulated
Support: 653252-face_attribute, 1947original, 416830-face_swap, 593986-face_swap, 1101341-orig, 2058original, 913-original

### image_text_consistency_assessment
Assess whether image content aligns with the text claim
Steps: Extract {claim_elements} (entities, event, location, date) from {text_claim}; Describe {image} main subject and scene; Assess alignment between {image} and {claim_elements}
Conditions: identities unconfirmable -> note uncertainty; scene matches event type -> consistent
Output: {consistency_finding}: {match, mismatch, uncertain}
Support: 89803-fake, 460533-real, 885904-fake, 653252-face_attribute, 593986-face_swap, 913-original

### manipulation_based_verdict
Render final verdict from manipulation finding and consistency
Steps: If {manipulation_finding} is manipulated -> judge Fake, cite manipulation type; If {manipulation_finding} is original and {consistency_finding} is match -> judge Real; Cite decisive evidence in rationale
Conditions: manipulation overrides consistency -> Fake; original + match -> Real
Output: {verdict} in {Real, Fake} with rationale citing manipulation type or consistency
Support: 653252-face_attribute, 593986-face_swap, 913-original

## Extracted decision rules

### context_refuted_fake_verdict
Extend refutation mechanisms to cover source misattribution and standard boilerplate precaution
Triggers: {context_evidence_finding} is refutes
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If refutes (including source misattribution or standard boilerplate precaution), judge Fake regardless of image-text match; Cite the refuting context evidence in the rationale
Conditions: refutes -> Fake (external refutation overrides alignment and tone); supports or insufficient -> route to other verdict rules
Evidence Rules: Refutation may rest on the cited source being a different document than claimed and the cited content being a standard boilerplate precaution
Decision Criteria: At least one relevant refuting source; image-text match and serious tone do not rescue a refuted claim
Uncertainty: Conflicting context evidence (some supports, some refutes) is not covered
Support: 16724-Refute, 6527-Refute, 14708-Refute, 22074-Refute, 5175-Refute, 29876-Refute

### visual_manipulation_screening
Detect image manipulation or AI generation as a prerequisite to verdict
Triggers: question asks about visual misinformation or manipulation; image accompanies a text claim
Steps: Examine {image} for manipulation artifacts: face swap, facial expression alteration, Photoshop edits; Determine whether {image} is AI-generated or sourced from a real photo; Record {manipulation_finding} (manipulated/original) and {ai_generated} (yes/no)
Conditions: manipulation detected -> flag as manipulated; no artifacts and real photo -> original
Evidence Rules: Manipulation type (face swap, expression edit) must be explicitly identified as the decisive evidence
Decision Criteria: Any confirmed manipulation -> image is not trustworthy for the claim
Uncertainty: Identity of persons in image cannot be confirmed from visual alone
Support: 653252-face_attribute, 1947original, 416830-face_swap, 593986-face_swap, 1101341-orig, 2058original, 913-original

### mismatch_verdict
Classify as Fake when the image depicts a different scene or entities than the claim, particularly when direct evidence confirms the actual event differs from the image
Triggers: image-text mismatch; direct evidence confirms actual event differs from image
Steps: Assess image-text consistency; If mismatch (different scene/entities), check direct evidence for the actual event; If direct evidence confirms the actual event differs from the image, classify as Fake
Conditions: image depicts different scene/entities than claimed -> mismatch; direct evidence confirms actual event differs from image -> Fake
Evidence Rules: direct evidence describing the actual event that differs from the image supports Fake
Decision Criteria: mismatch + direct evidence confirms different actual event -> Fake
Uncertainty: mismatch without direct evidence confirmation -> Insufficient
Support: 167300-fake

### inverse_evidence_subject_corroboration
Use inverse evidence that identifies the image's true subject, scene, or medium/genre to corroborate an image-text mismatch
Triggers: {consistency_finding} is mismatch
Steps: Compare {image_description} against {inverse_evidence} for subject, scene, or medium/genre identification; If {inverse_evidence} identifies a subject, scene, or medium (e.g., cartoon) different from {claim_elements}, record as mismatch corroboration
Conditions: inverse evidence names the actual image subject, scene, or medium -> corroborates mismatch; inverse evidence unrelated to image -> non_contributing
Evidence Rules: Inverse evidence may positively identify the true subject, scene, or medium of the image even when it does not address the text claim
Decision Criteria: Identified subject, scene, or medium differs from claimed content -> mismatch confirmed
Uncertainty: Inverse evidence suggesting but not naming the true subject/medium is not covered
Support: 93322-fake, 1567669-fake
