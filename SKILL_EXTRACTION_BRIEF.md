# Dataset-Only Skill Extraction Brief

You are helping design a system that **extracts** reusable multimodal-misinformation verification skills from the `NUSryan/TRUST-Instruct` dataset. Start from the dataset alone: do not rely on, search for, read, summarize, or use papers, pre-existing skills, externally authored verification workflows, retrieval evidence, or prior benchmark outputs to decide what the extracted skill should contain.

## Repository context and source boundary

This repository is a clean extraction workspace. Its relevant components are:

- `inspect_dataset.py` and `scripts/trust_instruct_*.py`: utilities for loading, sampling, and auditing TRUST-Instruct;
- the local Hugging Face cache: optional local access to TRUST-Instruct records and metadata;
- `SKILL_EXTRACTION_BRIEF.md`: this extraction specification.

Create all new extraction artifacts under `extraction/unified/`. The only permitted source of skill content is TRUST-Instruct and its metadata. Do not read unrelated data, evaluation files, results, skills, or external sources that may later be added to the repository.

## Research setting

The downstream task is multimodal misinformation classification. Each item contains a news-like image and text/caption. The target outcome is a binary credibility decision (`Real` or `Fake`) and, where applicable, one primary distortion type:

- `textual_veracity_distortion`: the textual claim is false, fabricated, misleading, falsely attributed, or otherwise factually distorted;
- `visual_veracity_distortion`: the image itself is materially manipulated, generated, or visually distorted;
- `cross_modal_consistency_distortion`: text and image may each be plausible in isolation but are paired with the wrong person, event, place, date, or context;
- `real`: no material distortion is identified.

This background defines the downstream task only. It is **not** a specification for the skill. The skill content, ordering, conditions, and wording must be induced from TRUST-Instruct examples.

## Objective

Develop an evidence-backed framework that reads TRUST-Instruct examples and extracts the reusable procedures demonstrated by the dataset. In this brief, a **trajectory** means one complete dataset example: its input, user instruction, and assistant response.

```text
input image/text/evidence/context
→ user instruction or question
→ assistant reasoning/output
→ decision or label
```

The framework must discover what the dataset actually teaches a model to inspect, compare, infer, and conclude. Do not start by writing a desired workflow and then look for examples that confirm it.

## Required operating constraints

1. Use TRUST-Instruct and its dataset metadata only as the source for induced skill content.
2. Do not use benchmark ground-truth labels, file paths, source names, or papers as hidden reasoning hints for a downstream evaluator.
3. Separate observations directly supported by examples from your own interpretation. Every proposed skill rule must retain provenance to representative dataset rows.
4. Do not use training examples verbatim as few-shot examples in the eventual evaluator. Extract abstract procedures, decision criteria, and output contracts instead.
5. Do not write a final skill until the inventory, example analysis, and extraction audit below are complete.

## Phase 1 — Inventory the dataset before interpreting it

Load the dataset and report its actual schema rather than assuming field names. Determine:

- configurations, splits, total row counts, and storage layout;
- every column, its type, null rate, and representative values;
- how images, captions/claims, evidence, metadata, conversations, labels, prompts, and assistant outputs are represented;
- conversation turn counts and role sequences;
- whether there are generic image-language rows distinct from misinformation-reasoning rows;
- all fields that could leak labels or provenance and therefore must not be available at downstream inference.

Produce a concise data card and save a reproducible row identifier for every inspected example.

## Phase 2 — Count examples and reasoning templates

Do not report one ambiguous number for “examples.” Report all of the following:

1. **Raw rows:** every dataset record.
2. **Reasoning examples:** records containing an input-to-assistant sequence relevant to the downstream task.
3. **Misinformation-reasoning examples:** the subset whose input/output actually teaches multimodal misinformation reasoning, rather than generic image description or alignment.
4. **Normalized reasoning templates:** unique reasoning structures after removing instance-specific entities, dates, locations, URLs, and label words while preserving the sequence of operations/questions.
5. **Distinct task prompts or instruction families:** normalized user-instruction patterns.

For each count, state the exact filtering and normalization rule, code or pseudocode used, and how duplicates were handled. If a record contains multiple assistant turns, it is still one example; describe its internal turn structure separately.

## Phase 3 — Extract structure from examples

For a stratified, reproducible sample of misinformation-reasoning examples, extract a structured record with these fields:

```text
row_id
input modalities and available fields
user instruction / question
assistant output sections or steps
atomic operation at each step
information consumed by that step
intermediate finding produced by that step
decision criterion or conditional rule
final output format
primary distortion type, if explicit in the example
confidence that this pattern is recurrent
```

Use an operation vocabulary that is discovered and revised from the data. Possible operations may include describing an image, identifying entities, analyzing a claim, comparing evidence, checking image-text relations, looking for visual anomalies, assessing stance, or making a final judgment—but retain an operation only if the dataset supports it.

Cluster examples by their normalized operation sequence, not merely by final label. For every cluster, provide:

- count and proportion;
- representative row IDs;
- common input fields and output structure;
- recurrent conditions, checks, and decision rules;
- variation within the cluster;
- which parts are clearly reusable versus instance-specific.

## Phase 4 — Incrementally extract one unified skill

This initial run must produce **only one unified skill**. Do not create the three distortion-specific skills yet.

Use an agentic workflow-memory pattern: maintain persistent artifacts on disk and update them after **every single eligible TRUST-Instruct example**. Do not rely on an ever-growing chat context or claim to remember previous rows without reading the saved state.

Maintain these artifacts:

```text
working_unified_skill.md     # current abstracted unified workflow
workflow_memory.jsonl        # one structured observation/update record per example
skill_change_log.jsonl       # every skill revision, reason, and supporting row IDs
progress.json                # dataset version, cursor, counts, and resumable state
```

For each eligible example, perform this loop in order:

1. Read the current `working_unified_skill.md` and persistent memory.
2. Inspect that example's input, instruction, and assistant output.
3. Extract any reusable operation, ordering constraint, conditional branch, evidence rule, decision criterion, or output-format rule demonstrated by the example.
4. Compare the observation against the current unified skill.
5. Choose exactly one action: `no_change`, `add_rule`, `generalize_rule`, `narrow_rule`, `reorder_steps`, or `remove_unsupported_rule`.
6. Update the unified skill only when the change is supported by the current example and does not contradict stronger accumulated evidence.
7. Append the observation, action, before/after rule text, and row ID to the memory and change log.
8. Persist progress before moving to the next example.

Guard against overfitting to one example: a new rule should remain tentative until it recurs in independent examples. Maintain support counts and supporting row IDs for every rule. If later examples conflict, preserve the conflict in memory and revise the rule only according to accumulated support, specificity, and recurrence.

The final unified skill must include:

```text
Skill name: Unified multimodal misinformation verification
Purpose
Trigger conditions inferred from data
Required inputs
Ordered procedure
Conditional branches
Evidence-handling rules
Decision criteria
Output contract
Known uncertainty / unsupported cases
Provenance: support counts and row IDs supporting every major rule
```

## Later phase — specialists only after unified extraction succeeds

After the unified extraction has been validated, run three separate incremental extraction passes over the same dataset using the same persistent-memory method:

1. `Check_textual_factuality` for textual-veracity distortion.
2. `Check_visual_manipulation` for visual-veracity distortion.
3. `Check_cross_modal_consistency` for cross-modal-consistency distortion.

Each specialist pass must create its own working skill, memory, change log, and progress file. Do not begin these passes during the unified-skill run.

## Phase 5 — Validate the unified extraction, not just its wording

Evaluate whether the unified skill faithfully compresses the dataset:

- Hold out a stratified set of examples before induction.
- For each held-out example, determine whether the extracted skill selects the same relevant operations and supports the same type of conclusion without copying the original answer.
- Measure coverage: percentage of examples represented by the unified skill/template.
- Identify unsupported rules, contradictions, and rare example types.
- Produce an extraction report with failures and proposed revisions.

## Deliverables before any benchmark run

Provide, in this order:

1. Dataset data card and schema.
2. Explicit example-count report using all five definitions above.
3. Normalized prompt/reasoning-template inventory.
4. Cluster analysis with representative row IDs.
5. The provenance-linked unified skill specification and its final `working_unified_skill.md`.
6. Holdout extraction-validation report.
7. A decision on whether the unified skill is ready before beginning the three specialist extraction passes.

## Quality bar

The result should make it possible to answer: “Which exact kinds of TRUST-Instruct examples caused this instruction, branch, rule, or output field to appear in the extracted skill?” If that question cannot be answered with dataset evidence, mark the rule as unsupported and omit it.
