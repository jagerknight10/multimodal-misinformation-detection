"""Offline tests for query-level Serper caching."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .serper import SerperError, cached_search


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"organic": [{"title": "example", "link": "https://example.org"}]}).encode()


class SerperCacheTests(unittest.TestCase):
    def test_cache_reuses_response_without_key_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            with patch("mmmisinfo.retrieval.serper.urlopen", return_value=Response()) as request:
                first, path, hit = cached_search("example claim", "search", cache_dir, "private-test-key")
                second, second_path, second_hit = cached_search("example claim", "search", cache_dir)
            self.assertEqual(request.call_count, 1)
            self.assertFalse(hit)
            self.assertTrue(second_hit)
            self.assertEqual(path, second_path)
            self.assertEqual(first, second)
            self.assertNotIn("private-test-key", path.read_text(encoding="utf-8"))

    def test_cache_miss_requires_key(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SerperError):
                cached_search("example claim", "search", Path(directory))

    def test_rejects_unknown_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                cached_search("example claim", "unknown", Path(directory), "key")


if __name__ == "__main__":
    unittest.main()
