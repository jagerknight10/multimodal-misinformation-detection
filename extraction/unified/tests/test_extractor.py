import json
import tempfile
import unittest
from pathlib import Path

from extraction.unified.src.clients import FixtureClient
from extraction.unified.src.extractor import (
    ACTIONS, build_prompt, make_batches, parse_json, to_trajectory, run_induction,
)
from extraction.unified.src.audit import audit_rows, normalize_text
from extraction.unified.src.grouping import group_items, select_representatives, operation_signature
from extraction.unified.src.loaders import load_fixture, load_representatives


FIXTURE = Path(__file__).parent / "fixtures/sample_rows.json"


class ExtractionTests(unittest.TestCase):
    def test_filtering_excludes_generic_rows(self):
        items = load_fixture(FIXTURE)
        self.assertEqual([item.row_id for item in items],
                         ["sample-visual", "sample-cross", "sample-text"])

    def test_batch_limit_and_prompt_content(self):
        items = load_fixture(FIXTURE)
        batches = make_batches(items, max_chars=500)
        self.assertGreaterEqual(len(batches), 2)
        prompt = build_prompt(batches[0], "", "")
        self.assertIn("sample-visual", prompt)
        self.assertIn("Return strict JSON", prompt)

    def test_json_parser_accepts_fenced_json(self):
        value = parse_json("```json\n{\"updates\": []}\n```")
        self.assertEqual(value, {"updates": []})
        self.assertEqual(parse_json("Here is the result:\n{\"updates\": []}"), {"updates": []})

    def test_resume_does_not_repeat_completed_batches(self):
        items = load_fixture(FIXTURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            client = FixtureClient()
            first = run_induction(items, client, output, max_chars=500)
            calls = client.calls
            self.assertEqual(first["api_calls"], calls)
            second = run_induction(items, client, output, max_chars=500)
            self.assertEqual(client.calls, calls)
            self.assertEqual(second["completed_batch"], first["completed_batch"])
            memory = (output / "workflow_memory.jsonl").read_text().splitlines()
            self.assertEqual(len(memory), len(items))

    def test_cache_prevents_repeat_model_calls(self):
        items = load_fixture(FIXTURE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            first_client = FixtureClient()
            run_induction(items, first_client, output, max_chars=500)
            second_client = FixtureClient()
            run_induction(items, second_client, output, max_chars=500)
            self.assertEqual(second_client.calls, 0)
            self.assertTrue((output / "cache/batch_0000.json").exists())

    def test_action_vocabulary_is_closed(self):
        self.assertIn("add_rule", ACTIONS)
        self.assertIsNotNone(to_trajectory({"id": "x", "image": "origin/x.jpg",
                                             "conversations": [
                                                 {"from": "human", "value": "visual misinformation"},
                                                 {"from": "gpt", "value": "response"},
                                             ]}))

    def test_audit_counts_and_normalizes_without_model(self):
        rows = json.loads(FIXTURE.read_text())
        report = audit_rows(rows)
        self.assertEqual(report["raw_rows"], 4)
        self.assertEqual(report["misinformation_reasoning_examples"], 3)
        self.assertEqual(report["family_counts"]["generic_image"], 1)
        self.assertEqual(normalize_text("Claim on 2024-01-02 https://example.com/7"),
                         "claim on {date} {url}")

    def test_grouping_is_deterministic_and_stratified(self):
        items = load_fixture(FIXTURE)
        groups = group_items(items)
        first = [item.row_id for item in select_representatives(groups, 1)]
        second = [item.row_id for item in select_representatives(group_items(items), 1)]
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(groups))
        self.assertIn("decompose_claim", operation_signature(items[1]))

    def test_representative_format_loads(self):
        items = load_representatives(FIXTURE.parent / "sample_representatives.json")
        self.assertEqual(items[0].row_id, "sample-visual")
        self.assertEqual(items[0].family, "visual")


if __name__ == "__main__":
    unittest.main()
