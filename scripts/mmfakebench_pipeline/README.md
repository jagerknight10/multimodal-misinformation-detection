# MMFakeBench evaluation pipeline

This pipeline does not download MMFakeBench. After the gated files are obtained,
run it with the split annotation JSON and the directory containing the split's
`real/` and `fake/` folders.

Set credentials in the root `.env` file. It is ignored by Git:

```bash
SOCLAAS_BASE_URL=https://soclaas-api.comp.nus.edu.sg
SOCLAAS_API_KEY=clsk_...
SOCLAAS_MODEL=qwen3-vl:32b
```

The pipeline loads `.env` automatically. Existing shell variables take precedence.

Commands may be run either as modules (`python3 -m ...`) or directly by file
path (`python3 scripts/mmfakebench_pipeline/smoke_test.py ...`).

Smoke test with an existing local image:

```bash
python3 -m scripts.mmfakebench_pipeline.smoke_test \
  --image tmp/pdfs/visual/trust.png \
  --caption "This image shows the TRUST-VL research workflow."
```

Check authentication and model access:

```bash
python3 -m scripts.mmfakebench_pipeline.check_api
```

If the gateway certificate is not trusted on your machine, install/use an
up-to-date CA bundle or set `SOCLAAS_CA_BUNDLE` explicitly. The client uses
`certifi` automatically when installed. Avoid `--insecure-tls` except for
isolated diagnostics.

Run the two conditions on a small sample:

```bash
python3 -m scripts.mmfakebench_pipeline.run \
  --annotations data/MMFakeBench_val/source/MMFakeBench_val.json \
  --image-root data/MMFakeBench_val --condition baseline \
  --limit 20 --concurrency 5 --output results/val_baseline.jsonl

python3 -m scripts.mmfakebench_pipeline.run \
  --annotations data/MMFakeBench_val/source/MMFakeBench_val.json \
  --image-root data/MMFakeBench_val --condition skill \
  --limit 20 --concurrency 3 --output results/val_skill.jsonl
```

Or run both matched conditions with one command:

```bash
python3 -m scripts.mmfakebench_pipeline.run_pair \
  --annotations data/MMFakeBench_val/source/MMFakeBench_val.json \
  --image-root data/MMFakeBench_val --limit 20 \
  --concurrency 5 --skill-concurrency 3 --output-dir results/val
```

Both conditions always receive the SoCLaaS `web_search_preview` tool so the comparison
uses identical retrieval access. The API key must be authorized for this tool.
Evaluate a JSONL file with:

```bash
python3 -m scripts.mmfakebench_pipeline.evaluate results/val_skill.jsonl
```

Compare matched conditions:

```bash
python3 -m scripts.mmfakebench_pipeline.compare \
  results/val/baseline.jsonl results/val/skill.jsonl
```

Each request is independent and bounded-concurrent. Results are appended as
JSONL immediately, so interrupted jobs can be retained and audited. Do not
commit the dataset, API key, or raw benchmark images.
