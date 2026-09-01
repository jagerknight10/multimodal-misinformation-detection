# Multimodal Misinformation Detection

This repository studies whether a structured, evidence-grounded skill can improve multimodal misinformation detection by guiding a vision-language model through the workflow proposed in TRUST-VL.

The implemented experiment compares the same model under controlled conditions:

1. Baseline: image, news caption, and fixed pre-retrieved TRUST-VL evidence.
2. Skill: the same image, caption, and evidence with the TRUST-VL-inspired verification skill.

The model, decoding settings, image inputs, evidence, and evaluation procedure remain fixed between runs. No live web search is performed during either evaluation condition.

## Repository contents

```text
.
├── inspect_dataset.py
├── skills/
│   └── trust-vl-multimodal-misinformation/
├── 2406.08772.pdf
├── 2409.07429.pdf
└── TRUST-VL Misinformation Detection.pdf
```

`inspect_dataset.py` streams TRUST-Instruct and displays generic Stage-1 image-instruction examples. The reusable skill is located at [`skills/trust-vl-multimodal-misinformation/SKILL.md`](skills/trust-vl-multimodal-misinformation/SKILL.md).

## Method

The skill follows the observable TRUST-VL workflow:

```text
Parse claim
→ analyze image independently
→ retrieve direct evidence from the text
→ retrieve inverse evidence from the image
→ check textual veracity
→ check visual integrity
→ check cross-modal consistency
→ produce a benchmark-compatible judgment
```

Direct evidence is retrieved from text-led searches. Inverse evidence is retrieved from image-derived entities, OCR, visible text, landmarks, captions, and reverse-image search when available. Evidence is recorded with its source, URL, date, relevance, and whether it supports or contradicts the claim.

The skill distinguishes three misinformation sources:

- `textual_veracity_distortion`
- `visual_veracity_distortion`
- `cross-modal_consistency_distortion`

It also supports the `real` class. A `Real` judgment requires the caption to be supported, the image not to be materially misleading, and the image to represent the claimed event.

## TRUST-Instruct

The Hugging Face [TRUST-Instruct dataset](https://huggingface.co/datasets/NUSryan/TRUST-Instruct) exposes one combined `train` split containing 1,409,577 rows. It combines:

- `TRUST-Instruct_task198k.json`: 198,253 misinformation-specific reasoning records.
- `trustvl_stage1_1211k.json`: approximately 1.211 million general image-language alignment records.

Only the 198K portion is used to derive the misinformation-verification workflow. The Stage-1 records are generic image-description examples and are not treated as misinformation reasoning supervision.

The dedicated records contain image paths and LLaVA-style conversations with combinations of:

- Claim analysis.
- Independent image description.
- Direct/context evidence comparison.
- Inverse evidence comparison.
- Tone or stance analysis.
- Image manipulation analysis.
- AI-generation assessment.
- Final `Real`/`Fake` judgment.

## MMFakeBench evaluation

[MMFakeBench](https://github.com/liuxuannan/MMFakeBench) provides mixed-source multimodal misinformation examples. Its annotation files are:

```text
MMFakeBench_val/source/MMFakeBench_val.json
MMFakeBench_test/source/MMFakeBench_test.json
```

Each annotation contains fields such as:

```json
{
  "text": "...",
  "image_path": "...",
  "text_source": "...",
  "image_source": "...",
  "gt_answers": "Fake",
  "fake_cls": "textual_veracity_distortion"
}
```

- `gt_answers` is the binary ground-truth field (the local validation file uses `True`/`False`; the TRUST-VL evidence manifest uses `real`/`fake`).
- `fake_cls` is the four-way misinformation-source label.

The first evaluation uses the validation split and the released TRUST-VL evidence manifest. The runner joins the evidence to the local validation images by exact caption text, caps direct and inverse evidence at 10 items each, and excludes the 8 evidence records without an exact caption match. This leaves 992 aligned records and 1,984 calls total: 992 baseline followed by 992 skill calls.

Predictions are checkpointed as JSONL with the sample ID, condition, local image path, evidence hash, raw response, parsed judgment/class, usage, SGT call timestamp, runtime, and errors. The live status file is `results/mmfakebench_status.md`. See [`scripts/mmfakebench_pipeline/README.md`](scripts/mmfakebench_pipeline/README.md) for commands.

The completed run produced the following paired results on 990 samples with parseable outputs in both conditions:

| Metric | Baseline | Skill |
|---|---:|---:|
| Binary accuracy | 75.86% | 76.26% |
| Binary macro-F1 | 0.719 | 0.656 |
| Four-way accuracy | 51.31% | 51.41% |
| Four-way macro-F1 | 0.456 | 0.519 |

The MMFakeBench files are gated on Hugging Face. Access and use must follow the authors' [dataset usage terms](https://huggingface.co/datasets/liuxuannan/MMFakeBench).

## Reproducibility requirements

- Use the same model checkpoint for both conditions.
- Use identical temperature, token limits, image preprocessing, and sample order.
- Keep web/search and image-search access consistent and document whether each condition has access to it.
- Store raw model outputs before parsing labels.
- Parse the final `Judgement: Real` or `Judgement: Fake` line separately from the explanation.
- Treat missing or inconclusive evidence as a recorded outcome, not as silently verified evidence.
- Do not use TRUST-Instruct examples as few-shot demonstrations during evaluation; use the distilled workflow only.

## Prior work

The project builds on the following work:

- Yan et al., [TRUST-VL: An Explainable News Assistant for General Multimodal Misinformation Detection](https://arxiv.org/abs/2509.04448), which introduces the shared/specialized reasoning taxonomy, evidence channels, QAVA, and TRUST-Instruct.
- [TRUST-Instruct](https://huggingface.co/datasets/NUSryan/TRUST-Instruct), the dataset used to study the structured reasoning traces.
- Liu et al., [MMFakeBench: A Mixed-Source Multimodal Misinformation Detection Benchmark for LVLMs](https://arxiv.org/abs/2406.08772), which defines the benchmark and its textual, visual, and cross-modal distortion categories.
- Wang et al., [Agent Workflow Memory](https://arxiv.org/abs/2409.07429), which motivates representing repeated agent behavior as reusable, abstract workflows.

TRUST-VL’s dataset construction draws on [Factify2](https://arxiv.org/abs/2304.03897), [DGM4](https://openaccess.thecvf.com/content/CVPR2023/html/Shao_Detecting_and_Grounding_Multi-Modal_Media_Manipulation_CVPR_2023_paper.html), [NewsCLIPpings](https://aclanthology.org/2021.emnlp-main.539/), [VisualNews](https://aclanthology.org/2021.emnlp-main.542/), [Fakeddit](https://aclanthology.org/2020.lrec-1.755/), and [LLaVA](https://arxiv.org/abs/2304.08485). These sources should be cited when their datasets or methods are directly used in future experiments.

