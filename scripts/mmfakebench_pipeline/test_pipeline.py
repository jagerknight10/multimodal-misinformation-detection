import json
import tempfile
import unittest
from pathlib import Path

try:
    from .compare import compare_rows
    from .data import load_evidence, select_stratified
    from .parse import parse_prediction
    from .prompts import BASELINE_INSTRUCTIONS, evidence_block, skill_instructions
    from .runner import run_condition
    from .status import StatusWriter
except ImportError:  # Allows unittest discovery with -s scripts/mmfakebench_pipeline.
    from compare import compare_rows
    from data import load_evidence, select_stratified
    from parse import parse_prediction
    from prompts import BASELINE_INSTRUCTIONS, evidence_block, skill_instructions
    from runner import run_condition
    from status import StatusWriter


class FakeClient:
    model = "fake-model"

    def __init__(self):
        self.calls = []

    def chat_completions_with_evidence(self, caption, image_path, evidence, instructions,
                                       temperature=0.0, max_tokens=1200):
        self.calls.append({"caption": caption, "image": image_path, "evidence": evidence,
                           "instructions": instructions})
        fake = "false" in caption
        label = "textual_veracity_distortion" if fake else "real"
        return {"choices": [{"message": {"content":
                f"Judgement: {'Fake' if fake else 'Real'}\nClass: {label}"}}],
                "usage": {"input_tokens": 1, "output_tokens": 1}}

    @staticmethod
    def text_from_chat_response(response):
        return response["choices"][0]["message"]["content"]


class PipelineTests(unittest.TestCase):
    def test_parser_requires_explicit_class_line(self):
        self.assertEqual(parse_prediction("realistic discussion\nJudgement: Fake\nClass: mismatch"),
                         {"predicted_binary": "Fake", "predicted_class": "cross_modal_consistency_distortion"})
        self.assertEqual(parse_prediction("This is realistic."),
                         {"predicted_binary": None, "predicted_class": None})

    def test_evidence_caps_labels_and_stratification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            rows = []
            for i, cls in enumerate(["original", "textual_veracity_distortion",
                                     "visual_veracity_distortion", "mismatch"]):
                rows.append({"question_id": str(i), "text": str(i), "image_path": "/trust.png",
                             "fake_cls": cls, "reference": "real" if cls == "original" else "fake",
                             "direct_evidence": [str(x) for x in range(12)],
                             "inverse_evidence": [str(x) for x in range(12)], "turns": ["ignore"]})
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            records = load_evidence(path)
            self.assertEqual(len(records[0]["direct_evidence"]), 10)
            self.assertEqual(records[0]["ground_truth_class"], "real")
            self.assertEqual(records[3]["ground_truth_class"], "cross_modal_consistency_distortion")
            self.assertEqual(len(select_stratified(records, 4)), 4)
            self.assertNotIn("turns", records[0])

    def test_alignment_uses_local_image_path_and_drops_unmatched(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            evidence = directory / "evidence.jsonl"
            annotations = directory / "annotations.json"
            evidence.write_text(json.dumps({"question_id": "a", "text": "same",
                "image_path": "/old/a.jpg", "fake_cls": "original", "reference": "real",
                "direct_evidence": [], "inverse_evidence": []}) + "\n" +
                json.dumps({"question_id": "b", "text": "missing", "image_path": "/old/b.jpg",
                "fake_cls": "original", "reference": "real", "direct_evidence": [],
                "inverse_evidence": []}) + "\n", encoding="utf-8")
            annotations.write_text(json.dumps([{"text": "same", "image_path": "/real/a.png",
                "fake_cls": "original", "gt_answers": "True"}]), encoding="utf-8")
            rows = load_evidence(evidence, annotations_path=annotations, drop_unmatched=True)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["image_path"], "/real/a.png")
            self.assertEqual(rows[0]["evidence_image_path"], "/old/a.jpg")

    def test_paired_run_same_evidence_and_resume(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            image = Path("tmp/pdfs/visual/trust.png").resolve()
            evidence_path = directory / "evidence.jsonl"
            rows = [{"question_id": "a", "text": "true", "image_path": "/trust.png",
                     "fake_cls": "original", "reference": "real", "direct_evidence": ["d"],
                     "inverse_evidence": ["i"]},
                    {"question_id": "b", "text": "false", "image_path": "/trust.png",
                     "fake_cls": "textual_veracity_distortion", "reference": "fake",
                     "direct_evidence": ["d2"], "inverse_evidence": ["i2"]}]
            evidence_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            records = load_evidence(evidence_path)
            status = StatusWriter(directory / "status.md", interval=1)
            status.start()
            try:
                run_condition(records, "baseline", image.parent, directory / "baseline.jsonl", status,
                              rpm=0, client=client)
                run_condition(records, "skill", image.parent, directory / "skill.jsonl", status,
                              rpm=0, client=client)
            finally:
                status.close(phase="test_done")
            self.assertEqual(len(client.calls), 4)
            self.assertEqual([call["evidence"] for call in client.calls[:2]],
                             [call["evidence"] for call in client.calls[2:]])
            baseline = [json.loads(line) for line in (directory / "baseline.jsonl").read_text().splitlines()]
            skill = [json.loads(line) for line in (directory / "skill.jsonl").read_text().splitlines()]
            self.assertEqual([row["evidence_hash"] for row in baseline],
                             [row["evidence_hash"] for row in skill])
            self.assertIn("Last updated (SGT)", (directory / "status.md").read_text())
            run_condition(records, "baseline", image.parent, directory / "baseline.jsonl", status,
                          rpm=0, client=client)
            self.assertEqual(len(client.calls), 4)

    def test_compare_rejects_different_evidence(self):
        row = {"sample_id": "a", "evidence_hash": "1", "predicted_binary": "Real",
               "predicted_class": "real", "ground_truth_binary": "Real",
               "ground_truth_class": "real"}
        other = dict(row, evidence_hash="2")
        with self.assertRaises(ValueError):
            compare_rows({"a": row}, {"a": other})

    def test_prompts_have_no_live_search_requirement(self):
        record = {"text": "claim", "direct_evidence": ["direct"], "inverse_evidence": ["inverse"]}
        self.assertIn("DIRECT TEXT-LED EVIDENCE", evidence_block(record))
        self.assertNotIn("web_search", BASELINE_INSTRUCTIONS)
        self.assertIn("Do not execute web search", skill_instructions())


if __name__ == "__main__":
    unittest.main()
