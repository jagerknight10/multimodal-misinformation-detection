# MMFakeBench three-condition evaluation

This pipeline evaluates the same vision-language model under three conditions:

1. `baseline`: image + caption + fixed TRUST-VL evidence.
2. `unified`: the same inputs + the unified TRUST-VL skill.
3. `routed`: the same inputs + one internal router and three specialist workflows.

The routed condition remains one API request per sample. Its system instructions
contain the router plus `Check_textual_factuality`, `Check_visual_manipulation`, and
`Check_cross_modal_consistency`; the model selects and executes the relevant workflow(s)
inside that response. It reports the selection in `Selected skills:` for later audit.

There are no live web-search calls during evaluation. The released
[TRUST-VL evidence manifest](https://github.com/YanZehong/TRUST-VL/blob/main/data/eval/MMFakeBench_1000.jsonl)
is loaded once. Direct evidence is capped at 10 items and inverse evidence at 10 items.
The `turns` field is excluded so training instructions are not leaked into evaluation.

## Data layout

Obtain the gated validation archive and annotation from the
[MMFakeBench dataset page](https://huggingface.co/datasets/liuxuannan/MMFakeBench),
then arrange the images as:

```text
data/MMFakeBench_val/
├── real/
├── fake/
└── source/MMFakeBench_val.json
```

The runner joins evidence to validation images by exact caption text. The current
released evidence file has 8 visual records without an exact caption match; these are
excluded and recorded in `run_config.json`, leaving 992 aligned records.

## Configuration

Put the SoCLaaS credentials in the root `.env`:

```bash
SOCLAAS_BASE_URL=https://soclaas-api.comp.nus.edu.sg
SOCLAAS_API_KEY=...
SOCLAAS_MODEL=qwen3-vl:32b
```

## Commands

Run the ten offline tests (these use a fake client and make no API calls):

```bash
python3 -m unittest scripts.mmfakebench_pipeline.test_pipeline -v
```

Run the 12-call smoke test (4 stratified records × 3 conditions):

```bash
python3 -m scripts.mmfakebench_pipeline.smoke_test \
  --evidence data/evidence/MMFakeBench_1000.jsonl \
  --annotations data/MMFakeBench_val/source/MMFakeBench_val.json \
  --image-root data/MMFakeBench_val \
  --output-dir results/strong_model_smoke \
  --rpm 10 --timeout 240 --temperature 0 --max-output-tokens 1200
```

After selecting the stronger model, run the full aligned validation
(992 × 3 = 2,976 calls):

```bash
python3 -m scripts.mmfakebench_pipeline.run_three \
  --evidence data/evidence/MMFakeBench_1000.jsonl \
  --annotations data/MMFakeBench_val/source/MMFakeBench_val.json \
  --image-root data/MMFakeBench_val \
  --output-dir results/strong_model_full_992 \
  --smoke-config results/strong_model_smoke/run_config.json \
  --selection first --concurrency 3 --rpm 10 \
  --timeout 240 --max-retries 1 --temperature 0 --max-output-tokens 1200
```

Each condition writes checkpointed JSONL results immediately. The runner records the
caption, local image path, original evidence path, evidence hash, raw response,
parsed labels, selected specialists, prompt/skill hashes, usage, call start time in
SGT, duration, and errors. The full runner first verifies that the four-sample smoke
run completed successfully with the same model, settings, evidence, and canonical
skill files. A call is bounded
below five minutes; if one exceeds five minutes, new API calls are stopped. Live
status is written to `results/mmfakebench_status.md`.

Reparse saved responses after parser changes without making API calls:

```bash
python3 -m scripts.mmfakebench_pipeline.reparse \
  results/strong_model_full_992/baseline.jsonl results/strong_model_full_992/baseline_reparsed.jsonl
python3 -m scripts.mmfakebench_pipeline.reparse \
  results/strong_model_full_992/unified.jsonl results/strong_model_full_992/unified_reparsed.jsonl
python3 -m scripts.mmfakebench_pipeline.reparse \
  results/strong_model_full_992/routed.jsonl results/strong_model_full_992/routed_reparsed.jsonl
```

Compare matched outputs:

```bash
python3 -m scripts.mmfakebench_pipeline.compare_three \
  results/strong_model_full_992/baseline_reparsed.jsonl \
  results/strong_model_full_992/unified_reparsed.jsonl \
  results/strong_model_full_992/routed_reparsed.jsonl \
  --output results/strong_model_full_992/comparison_reparsed.json
```

Create a row-by-row side-by-side summary, including all three raw responses and the
routed skill selection:

```bash
python3 -m scripts.mmfakebench_pipeline.summarize_three \
  results/strong_model_full_992/baseline_reparsed.jsonl \
  results/strong_model_full_992/unified_reparsed.jsonl \
  results/strong_model_full_992/routed_reparsed.jsonl \
  results/strong_model_full_992/side_by_side_summary.json
```

The comparison reports binary accuracy and macro-F1, four-way accuracy and macro-F1,
confusion matrices, each ground-truth distortion slice, real-versus-distortion binary
cohorts, paired improvements/regressions, and routing-selection statistics.
The side-by-side summary also indexes representative improvements, regressions,
all-correct/all-wrong cases, and routed outputs that omitted a skill selection.

## Historical two-condition run

The earlier Qwen3-VL-32B run produced 992 rows per condition, 1,984 successful API calls, and
zero API errors. Two skill responses were truncated before producing parseable labels;
final paired metrics therefore use the same 990 complete samples:

| Metric | Baseline | Skill | Change |
|---|---:|---:|---:|
| Binary accuracy | 75.86% | 76.26% | +0.40 pp |
| Binary macro-F1 | 0.719 | 0.656 | -0.063 |
| Four-way accuracy | 51.31% | 51.41% | +0.10 pp |
| Four-way macro-F1 | 0.456 | 0.519 | +0.063 |

These are benchmark results, not conclusions about general model quality. Inspect
class-wise metrics and raw responses before interpreting the effect of the skill.
