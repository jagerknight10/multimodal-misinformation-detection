# Project Python modules

The repository's Python code is grouped by responsibility:

- `benchmark/`: MMFakeBench inputs, prompts, provider adapters, runners, metrics, and tests.
- `retrieval/`: cached online evidence retrieval and its smoke test.
- `trust_instruct/`: dataset inspection, sampling, and consistency analysis.

Run entry points as modules from the repository root:

```bash
python3 -m mmmisinfo.benchmark.run --help
python3 -m mmmisinfo.trust_instruct.trust_instruct_overview --help
python3 -m mmmisinfo.retrieval.serper_smoke --help
```

See `benchmark/README.md` and `retrieval/README.md` for task-specific commands.

Offline checks:

```bash
python3 -m unittest mmmisinfo.benchmark.test_pipeline mmmisinfo.retrieval.test_serper -v
```
