# Check_textual_factuality

## Scope

Assess textual factuality and context support/refutation using only the supplied task inputs and evidence.

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

### context_evidence_relevance_screening
Decide whether supplied context evidence can support or refute the text claim
Steps: Read {context_evidence} and identify content type; Check relevance to {claim_elements}; If boilerplate (page-not-found, newsletter signup, generic site text) mark insufficient; Otherwise classify as supports or refutes {text_claim}
Conditions: boilerplate or unrelated -> insufficient/non_contributing; relevant -> supports or refutes
Output: {context_evidence_finding} in {supports, refutes, insufficient}
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal

### tone_satire_screening
Detect satire or parody in the text as a refutation signal
Steps: Read {text_claim}; Classify tone as serious/factual or satirical/parody; If no satire indicated, record no refutation signal
Conditions: satirical or parody -> refutation signal; serious factual -> no refutation signal
Output: {tone_finding} in {serious, satirical}
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal

### alignment_only_real_verdict
Render a verdict when image-text matches but external evidence is insufficient
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If match + insufficient + serious, judge Real; Note verdict rests on image alignment, not external confirmation
Conditions: match + insufficient + serious -> Real (alignment only); mismatch or satirical tone -> route to mismatch overrides
Output: {verdict} in {Real, Fake} with rationale stating the basis
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal

### context_confirmed_real_verdict
Render a verdict when image-text matches and context evidence supports the claim
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If match + supports + serious, judge Real; Cite the supporting context evidence in the rationale
Conditions: match + supports + serious -> Real (externally confirmed); mismatch or satirical tone -> route to mismatch overrides
Output: {verdict} in {Real, Fake} with rationale citing supporting evidence
Support: 6744-Support_Multimodal, 4250-Support_Multimodal

### context_refuted_fake_verdict
Render Fake when external context evidence refutes the claim, overriding image-text alignment
Steps: Extract {claim_elements} (actor, action, affiliation, location, date) from {text_claim}; Describe {image} and assess image-text consistency; Screen {context_evidence} for relevance to {claim_elements}; classify as supports/refutes/insufficient; Classify {tone_finding} as serious or satirical; If {context_evidence_finding} is refutes, judge Fake and cite the refuting evidence in the rationale
Conditions: refutes -> Fake regardless of image-text match or tone; supports or insufficient -> route to other verdict rules
Output: {verdict} in {Real, Fake} with rationale citing the refuting context evidence
Support: 16724-Refute, 5175-Refute

## Extracted decision rules

### boilerplate_context_evidence_screening
Determine whether supplied context evidence can support or refute the text claim before it enters verdict aggregation
Triggers: context evidence present in trajectory
Steps: Read {context_evidence} and identify its content type; Check relevance to {claim_elements}; If boilerplate (page-not-found, newsletter signup, generic site text) mark insufficient; Otherwise classify as supports or refutes {text_claim}
Conditions: evidence is boilerplate or unrelated -> insufficient/non_contributing; evidence is relevant -> supports or refutes
Evidence Rules: boilerplate evidence must not be treated as support or refutation
Decision Criteria: relevance to {claim_elements} determines contribution
Uncertainty: relevant but ambiguous evidence is not covered by this batch
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal

### tone_satire_screening
Classify light-hearted but sincere tone as serious rather than satirical
Triggers: text claim present
Steps: Read {text_claim}; Classify tone as serious/factual or satirical/parody; Treat light-hearted but sincere tone as serious (no refutation signal)
Conditions: satirical or parody markers -> refutation signal; light-hearted but sincere -> serious
Evidence Rules: tone is assessed from text alone, not from image
Decision Criteria: presence of parody/satire markers, not mere lightness
Uncertainty: subtle sarcasm detection is not demonstrated in this batch
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal, 6744-Support_Multimodal

### alignment_only_real_verdict
Render a verdict when image-text matches but external evidence is insufficient
Triggers: {consistency_finding} is match and {context_evidence_finding} is insufficient
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If match + insufficient + serious, judge Real; Note verdict rests on image alignment, not external confirmation
Conditions: match + insufficient + serious -> Real (alignment only); mismatch or satirical tone -> route to mismatch overrides
Evidence Rules: absence of contrary evidence plus visual match suffices for Real in this pattern
Decision Criteria: no refutation signal from any channel
Uncertainty: whether alignment-only Real should be downgraded to inconclusive is unresolved
Support: 6031-Support_Multimodal, 15681-Support_Multimodal, 3573-Support_Multimodal

### context_confirmed_real_verdict
Render Real when external context evidence supports the claim in addition to image-text alignment
Triggers: {consistency_finding} is match and {context_evidence_finding} is supports
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If match + supports + serious, judge Real; State verdict rests on visual alignment plus external confirmation
Conditions: match + supports + serious -> Real (externally confirmed); mismatch or satirical tone -> route to mismatch overrides
Evidence Rules: supporting context evidence must be relevant to {claim_elements} and non-boilerplate
Decision Criteria: no refutation signal from any channel and at least one relevant supporting source
Uncertainty: single-source support without independent corroboration is not covered
Support: 6744-Support_Multimodal, 4250-Support_Multimodal

### context_refuted_fake_verdict
Extend refutation mechanisms to cover source misattribution and standard boilerplate precaution
Triggers: {context_evidence_finding} is refutes
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If refutes (including source misattribution or standard boilerplate precaution), judge Fake regardless of image-text match; Cite the refuting context evidence in the rationale
Conditions: refutes -> Fake (external refutation overrides alignment and tone); supports or insufficient -> route to other verdict rules
Evidence Rules: Refutation may rest on the cited source being a different document than claimed and the cited content being a standard boilerplate precaution
Decision Criteria: At least one relevant refuting source; image-text match and serious tone do not rescue a refuted claim
Uncertainty: Conflicting context evidence (some supports, some refutes) is not covered
Support: 16724-Refute, 6527-Refute, 14708-Refute, 22074-Refute, 5175-Refute, 29876-Refute

### inconclusive_insufficient_verdict
Render Insufficient when image-text consistency is inconclusive and context evidence is insufficient, even with serious tone
Triggers: {consistency_finding} is inconclusive; {context_evidence_finding} is insufficient
Steps: Collect {consistency_finding}, {context_evidence_finding}, {tone_finding}; If consistency is inconclusive (image neutral/unrelated to {claim_elements}) and context is insufficient, judge Insufficient; Note that serious tone alone does not confirm the claim
Conditions: inconclusive + insufficient -> Insufficient; match + insufficient + serious -> Real (not externally confirmed); refutes -> Fake
Evidence Rules: unrelated boilerplate news roundup is insufficient/non-contributing; neutral image lacking a direct visual link to {claim_elements} is inconclusive, not a match
Decision Criteria: no direct visual evidence and no relevant supporting or refuting context -> Insufficient
Uncertainty: whether a neutral image plus serious tone should count as a match is unresolved
Support: 23578-Support_Multimodal
