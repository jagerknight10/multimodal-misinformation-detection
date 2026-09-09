import json
import tempfile
import unittest
from pathlib import Path

try:
    from .compare import compare_conditions, compare_rows
    from .data import load_evidence, select_stratified
    from .experiment import (build_run_config, validate_completed_smoke,
                             write_run_config)
    from .parse import parse_prediction
    from .prompts import (BASELINE_INSTRUCTIONS, evidence_block,
                          instructions_for_condition, routed_skill_instructions,
                          skill_instructions)
    from .runner import run_condition
    from .status import StatusWriter
    from .summarize_three import summarize
except ImportError:  # Allows unittest discovery with -s scripts/mmfakebench_pipeline.
    from compare import compare_conditions, compare_rows
    from data import load_evidence, select_stratified
    from experiment import (build_run_config, validate_completed_smoke,
                            write_run_config)
    from parse import parse_prediction
    from prompts import (BASELINE_INSTRUCTIONS, evidence_block,
                         instructions_for_condition, routed_skill_instructions,
                         skill_instructions)
    from runner import run_condition
    from status import StatusWriter
    from summarize_three import summarize


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
        selected = ("Selected skills: Check_textual_factuality\n"
                    if "ROUTING WORKFLOW" in instructions else "")
        return {"choices": [{"message": {"content":
                f"{selected}Judgement: {'Fake' if fake else 'Real'}\nClass: {label}"}}],
                "usage": {"input_tokens": 1, "output_tokens": 1}}

    @staticmethod
    def text_from_chat_response(response):
        return response["choices"][0]["message"]["content"]


class PipelineTests(unittest.TestCase):
    def test_parser_requires_explicit_class_line(self):
        self.assertEqual(parse_prediction("realistic discussion\nJudgement: Fake\nClass: mismatch"),
                         {"predicted_binary": "Fake",
                          "predicted_class": "cross_modal_consistency_distortion",
                          "selected_skills": [], "reported_confidence": None})
        self.assertEqual(parse_prediction("This is realistic."),
                         {"predicted_binary": None, "predicted_class": None,
                          "selected_skills": [], "reported_confidence": None})

    def test_parser_reads_routed_specialists(self):
        parsed = parse_prediction(
            "Selected skills: Check_visual_manipulation, Check_cross_modal_consistency\n"
            "Confidence: High\nJudgement: Fake\nClass: visual_veracity_distortion")
        self.assertEqual(parsed["selected_skills"], [
            "Check_visual_manipulation", "Check_cross_modal_consistency"])
        self.assertEqual(parsed["reported_confidence"], "High")

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

    def test_three_condition_run_same_evidence_and_resume(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            image = Path("tmp/pdfs/visual/trust.png").resolve()
            evidence_path = directory / "evidence.jsonl"
            rows = []
            classes = ("original", "textual_veracity_distortion",
                       "visual_veracity_distortion", "mismatch")
            for index, class_name in enumerate(classes):
                rows.append({
                    "question_id": str(index),
                    "text": "true" if index == 0 else f"false {index}",
                    "image_path": "/trust.png", "fake_cls": class_name,
                    "reference": "real" if index == 0 else "fake",
                    "direct_evidence": [f"d{index}"],
                    "inverse_evidence": [f"i{index}"],
                })
            evidence_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            records = load_evidence(evidence_path)
            smoke_config = build_run_config(
                "smoke", evidence_path, directory / "annotations.json", image.parent,
                4, client.model, 0.0, 1200, 0, 1)
            smoke_config_path = write_run_config(smoke_config, directory)
            status = StatusWriter(directory / "status.md", interval=1)
            status.start()
            try:
                run_condition(records, "baseline", image.parent, directory / "baseline.jsonl", status,
                              rpm=0, client=client)
                run_condition(records, "unified", image.parent,
                              directory / "unified.jsonl", status, rpm=0, client=client)
                run_condition(records, "routed", image.parent,
                              directory / "routed.jsonl", status, rpm=0, client=client)
            finally:
                status.close(phase="test_done")
            self.assertEqual(len(client.calls), 12)
            self.assertEqual([call["evidence"] for call in client.calls[:4]],
                             [call["evidence"] for call in client.calls[4:8]])
            self.assertEqual([call["evidence"] for call in client.calls[:4]],
                             [call["evidence"] for call in client.calls[8:]])
            baseline = [json.loads(line) for line in (directory / "baseline.jsonl").read_text().splitlines()]
            unified = [json.loads(line) for line in (directory / "unified.jsonl").read_text().splitlines()]
            routed = [json.loads(line) for line in (directory / "routed.jsonl").read_text().splitlines()]
            self.assertEqual([row["evidence_hash"] for row in baseline],
                             [row["evidence_hash"] for row in unified])
            self.assertEqual([row["evidence_hash"] for row in baseline],
                             [row["evidence_hash"] for row in routed])
            self.assertEqual(routed[0]["selected_skills"], ["Check_textual_factuality"])
            full_config = build_run_config(
                "full", evidence_path, directory / "annotations.json", image.parent,
                992, client.model, 0.0, 1200, 10, 3)
            checked = validate_completed_smoke(smoke_config_path, full_config)
            self.assertEqual(checked["calls"], 12)
            self.assertIn("Last updated (SGT)", (directory / "status.md").read_text())
            run_condition(records, "baseline", image.parent, directory / "baseline.jsonl", status,
                          rpm=0, client=client)
            self.assertEqual(len(client.calls), 12)

    def test_compare_rejects_different_evidence(self):
        row = {"sample_id": "a", "evidence_hash": "1", "predicted_binary": "Real",
               "predicted_class": "real", "ground_truth_binary": "Real",
               "ground_truth_class": "real"}
        other = dict(row, evidence_hash="2")
        with self.assertRaises(ValueError):
            compare_rows({"a": row}, {"a": other})

    def test_resume_rejects_a_different_model(self):
        first_client = FakeClient()
        second_client = FakeClient()
        second_client.model = "different-model"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            record = {"sample_id": "a", "index": 0, "text": "true",
                      "image_path": "/trust.png", "ground_truth_binary": "Real",
                      "ground_truth_class": "real", "direct_evidence": [],
                      "inverse_evidence": [], "evidence_hash": "same"}
            status = StatusWriter(directory / "status.md", interval=1)
            status.start()
            output = directory / "baseline.jsonl"
            try:
                run_condition([record], "baseline", Path("tmp/pdfs/visual"), output,
                              status, rpm=0, client=first_client)
                with self.assertRaises(ValueError):
                    run_condition([record], "baseline", Path("tmp/pdfs/visual"), output,
                                  status, rpm=0, client=second_client)
            finally:
                status.close(phase="test_done")
            self.assertEqual(len(second_client.calls), 0)

    def test_three_condition_comparison_and_subsets(self):
        base = {"sample_id": "a", "evidence_hash": "1", "predicted_binary": "Real",
                "predicted_class": "real", "ground_truth_binary": "Fake",
                "ground_truth_class": "textual_veracity_distortion", "error": None}
        unified = dict(base, predicted_binary="Fake",
                       predicted_class="textual_veracity_distortion")
        routed = dict(unified, selected_skills=["Check_textual_factuality"])
        result = compare_conditions({"baseline": {"a": base},
                                     "unified": {"a": unified},
                                     "routed": {"a": routed}})
        self.assertEqual(result["paired_rows"], 1)
        self.assertEqual(result["binary"]["routed"]["accuracy"], 1.0)
        self.assertEqual(result["by_ground_truth_class"]
                         ["textual_veracity_distortion"]["n"], 1)
        self.assertEqual(result["routing"]["gold_distortion_skill_included"], 1)

    def test_three_way_summary_indexes_representative_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            common = {"sample_id": "a", "index": 0, "evidence_hash": "same",
                      "ground_truth_binary": "Fake",
                      "ground_truth_class": "textual_veracity_distortion",
                      "error": None}
            rows = {
                "baseline": dict(common, predicted_binary="Real", predicted_class="real"),
                "unified": dict(common, predicted_binary="Fake",
                                predicted_class="textual_veracity_distortion"),
                "routed": dict(common, predicted_binary="Fake",
                               predicted_class="textual_veracity_distortion",
                               selected_skills=["Check_textual_factuality"]),
            }
            paths = {}
            for name, row in rows.items():
                paths[name] = directory / f"{name}.jsonl"
                paths[name].write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = summarize(paths["baseline"], paths["unified"], paths["routed"])
            self.assertEqual(result["sample_count"], 1)
            self.assertEqual(result["representative_case_ids"]
                             ["routed_binary_improves_over_baseline"]["first_10"], ["a"])

    def test_prompts_have_no_live_search_requirement(self):
        record = {"text": "claim", "direct_evidence": ["direct"], "inverse_evidence": ["inverse"]}
        self.assertIn("DIRECT TEXT-LED EVIDENCE", evidence_block(record))
        self.assertNotIn("web_search", BASELINE_INSTRUCTIONS)
        self.assertIn("Do not execute web search", skill_instructions())
        routed = routed_skill_instructions()
        self.assertIn("ROUTING WORKFLOW", routed)
        self.assertIn("Check_textual_factuality", routed)
        self.assertIn("Check_visual_manipulation", routed)
        self.assertIn("Check_cross_modal_consistency", routed)
        self.assertIn("single response", routed)
        self.assertEqual(instructions_for_condition("skill"), skill_instructions())
        with self.assertRaises(ValueError):
            instructions_for_condition("unknown")


if __name__ == "__main__":
    unittest.main()
