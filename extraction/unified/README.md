# Unified workflow extraction

This directory contains the offline, AWM-style extraction prototype for
TRUST-Instruct. Dataset inspection and persistence are local; model induction
operates on grouped, bounded batches rather than one API call per row.

Run offline tests from the repository root:

```bash
python3 -m unittest discover -s extraction/unified/tests -v
```

Run a small deterministic dry run:

```bash
python3 extraction/unified/scripts/run_induction.py \
  --fixture extraction/unified/tests/fixtures/sample_rows.json \
  --output-dir /tmp/trust-unified-smoke \
  --batch-size 3 \
  --dry-run
```

The live SOCLaAS mode is deliberately opt-in:

```bash
python3 extraction/unified/scripts/run_induction.py \
  --fixture extraction/unified/tests/fixtures/sample_rows.json \
  --output-dir /tmp/trust-unified-live \
  --batch-size 3 \
  --provider soclaas
```

## Persistent induction artifacts

Each accepted model response is materialized into four complementary outputs:

- `working_unified_skill.md`: human-readable synthesized skill.
- `rule_ledger.json`: structured rules with all requested fields and provenance.
- `workflow_catalog.json`: reusable workflows with steps, conditions, output contracts, and supporting rows.
- `workflow_memory.jsonl`: per-batch observations and model memory.
- `skill_change_log.jsonl`: accepted changes only; `no_change` observations are not recorded here.

The runner caches each response under `<output-dir>/cache/` and resumes from
`progress.json`. To continue the current SOCLaAS run from its existing cache:

```bash
python3 extraction/unified/scripts/run_induction.py \
  --representatives extraction/unified/artifacts/representatives.json \
  --output-dir extraction/unified/artifacts/induction_qwen3_8_small \
  --batch-size 6500 \
  --provider soclaas \
  --model qwen3.8:27b
```

The existing cached responses can be materialized again without API calls using:

```bash
python3 extraction/unified/scripts/rebuild_artifacts.py \
  --output-dir extraction/unified/artifacts/induction_qwen3_8_small
```

For a shorter modality-preserving run, generate one stable representative per
semantic group. This retains rare groups and all modality families:

```bash
python3 extraction/unified/scripts/sample_trajectories.py \
  --cache-dir .cache \
  --output-dir extraction/unified/artifacts/representatives_sampled \
  --per-group 1
```

Then start a fresh seeded run. The old run remains untouched, while its skill,
ledgers, and workflow memory provide context without reprocessing its batches:

```bash
python3 extraction/unified/scripts/run_induction.py \
  --representatives extraction/unified/artifacts/representatives_sampled/representatives.json \
  --output-dir extraction/unified/artifacts/induction_qwen3_8_sampled \
  --seed-dir extraction/unified/artifacts/induction_qwen3_8_small \
  --batch-size 6500 \
  --provider soclaas \
  --model qwen3.8:27b
```
