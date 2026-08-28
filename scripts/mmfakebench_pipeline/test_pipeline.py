import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .parse import parse_prediction
from .run import main as run_main
from .soclaas import SoCLaaSClient


class PipelineSmokeTests(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(parse_prediction("Judgement: Fake\nClass: visual_veracity_distortion"), {
            "predicted_binary": "Fake",
            "predicted_class": "visual_veracity_distortion",
        })
        self.assertEqual(parse_prediction("Finish[MISMATCH].")["predicted_binary"], "Fake")

    def test_image_encoding(self):
        client = SoCLaaSClient(base_url="http://mock", api_key="test")
        encoded = client.image_data_url("tmp/pdfs/visual/trust.png")
        self.assertTrue(encoded.startswith("data:image/png;base64,"))

    def test_concurrent_run_and_resume(self):
        calls = []

        def fake_response(client, caption, image_path, instructions, tools=None,
                          temperature=0.0, max_output_tokens=1200):
            calls.append((caption, tools))
            fake = "false" in caption
            return {
                "output_text": ("Judgement: Fake\nClass: textual_veracity_distortion" if fake
                                else "Judgement: Real\nClass: real"),
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            annotation_path = directory / "annotations.json"
            output_path = directory / "predictions.jsonl"
            annotation_path.write_text(json.dumps([
                {"text": "true", "image_path": "/trust.png", "gt_answers": "Real", "fake_cls": "real"},
                {"text": "false", "image_path": "/trust.png", "gt_answers": "Fake",
                 "fake_cls": "textual_veracity_distortion"},
            ]))
            os.environ.update({"SOCLAAS_BASE_URL": "http://mock", "SOCLAAS_API_KEY": "test"})
            arguments = ["run", "--annotations", str(annotation_path), "--image-root", "tmp/pdfs/visual",
                         "--condition", "baseline", "--output", str(output_path), "--concurrency", "2"]
            with patch.object(SoCLaaSClient, "responses", fake_response):
                with patch.object(sys, "argv", arguments):
                    run_main()
                with patch.object(sys, "argv", arguments):
                    run_main()
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(tools == [{"type": "web_search_preview"}] for _, tools in calls))
            self.assertEqual(len(output_path.read_text().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
