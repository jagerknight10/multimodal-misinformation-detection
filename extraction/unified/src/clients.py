"""Model client adapters for live and offline extraction."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


class SoCLaaSTextClient:
    def __init__(self, model=None):
        from mmfakebench_pipeline.soclaas import SoCLaaSClient
        self._client = SoCLaaSClient(model=model)
        self.model = self._client.model

    def generate(self, prompt: str) -> str:
        response = self._client.responses_text(
            prompt,
            "Extract workflows from the supplied dataset trajectories. Return only compact requested JSON; do not show reasoning or repeat the trajectories.",
            max_output_tokens=4000,
        )
        text = self._client.text_from_response(response)
        if not text:
            raise RuntimeError(
                f"SOCLaAS returned no visible text (status={response.get('status')!r}, "
                f"output_items={len(response.get('output', []))})"
            )
        return text


class FixtureClient:
    """Deterministic test client; each call returns a valid batch response."""
    model = "fixture"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> str:
        import json
        import re
        self.calls += 1
        ids = re.findall(r"row_id: ([^\n]+)", prompt)
        updates = [{"row_id": row_id, "action": "no_change",
                    "observation": "fixture observation", "rule": "",
                    "supporting_row_ids": [row_id]} for row_id in ids]
        return json.dumps({
            "working_skill": "Fixture unified skill",
            "updates": updates,
            "workflows": [],
        })
