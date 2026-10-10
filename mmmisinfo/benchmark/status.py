"""Small live Markdown status writer for long-running benchmark jobs."""

from datetime import datetime
from pathlib import Path
from threading import Event, Lock, Thread
from zoneinfo import ZoneInfo


SGT = ZoneInfo("Asia/Singapore")


class StatusWriter:
    def __init__(self, path, interval=30):
        self.path = Path(path)
        self.interval = interval
        self.state = {"phase": "starting"}
        self.lock = Lock()
        self.stop_event = Event()
        self.thread = None

    def _timestamp(self):
        return datetime.now(SGT).isoformat(timespec="seconds")

    def update(self, **values):
        with self.lock:
            self.state.update(values)
            self.state["last_updated_sgt"] = self._timestamp()
            snapshot = dict(self.state)
        self._write(snapshot)

    def _write(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# MMFakeBench run status", "",
            f"- Last updated (SGT): `{state.get('last_updated_sgt', self._timestamp())}`",
            f"- Phase: `{state.get('phase', 'unknown')}`",
            f"- Condition: `{state.get('condition', '-')}`",
            f"- Completed: `{state.get('completed', 0)}/{state.get('total', 0)}`",
            f"- Pending: `{state.get('pending', '-')}`",
            f"- API calls completed: `{state.get('api_calls', 0)}`",
            f"- Errors: `{state.get('errors', 0)}`",
            f"- Current sample: `{state.get('current_sample', '-')}`",
            f"- Last call started (SGT): `{state.get('last_call_started_sgt', '-')}`",
            f"- Last call duration (seconds): `{state.get('last_call_duration_seconds', '-')}`",
            f"- Rate limit: `{state.get('rpm', '-')}` requests/minute",
            "",
            state.get("message", ""),
            "",
        ]
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text("\n".join(lines), encoding="utf-8")
        temporary.replace(self.path)

    def start(self):
        self.update()
        self.thread = Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stop_event.wait(self.interval):
            with self.lock:
                snapshot = dict(self.state)
                snapshot["last_updated_sgt"] = self._timestamp()
            self._write(snapshot)

    def close(self, **values):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        self.update(**values)
