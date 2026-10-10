# Online evidence retrieval

`serper.py` contains the Serper client and query-level disk cache. A cached query
can be replayed without an API key or another API request. Cache records include
the request, timestamp, HTTP status, and full response, but never the API key.

Run one text or image search from the repository root:

```bash
python3 -m mmmisinfo.retrieval.serper_smoke --query "Chrysler Building surpassed in height"
python3 -m mmmisinfo.retrieval.serper_smoke --endpoint images --query "Obama walking outdoors blue tie"
```

Set `SERPER_API_KEY` in the environment or enter it at the prompt on a cache miss.
The default cache is `data/evidence/serper_smoke/`. This is a smoke tool, not a
benchmark-wide collector. It never launches a bulk retrieval run.

Offline tests:

```bash
python3 -m unittest mmmisinfo.retrieval.test_serper -v
```
