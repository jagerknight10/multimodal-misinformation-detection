"""Shared-evidence, paired-condition benchmark execution."""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .data import resolve_image
from .parse import parse_prediction
from .prompts import evidence_block, instructions_for_condition, prompt_manifest
from .soclaas import SoCLaaSClient


SGT = ZoneInfo("Asia/Singapore")


class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0 / rpm if rpm and rpm > 0 else 0.0
        self.next_time = 0.0
        self.lock = threading.Lock()

    def acquire(self):
        while True:
            with self.lock:
                wait = max(0.0, self.next_time - time.monotonic())
                if wait == 0:
                    self.next_time = time.monotonic() + self.interval
                    return
            time.sleep(min(wait, 1.0))


def _sgt_now():
    return datetime.now(SGT).isoformat(timespec="seconds")


def _read_successful(path):
    completed = {}
    if not Path(path).exists():
        return completed
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("sample_id") and not row.get("error"):
                completed[row["sample_id"]] = row
    return completed


def write_manifest(records, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in records:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_condition(records, condition, image_root, output, status, rpm=10,
                  concurrency=1, max_output_tokens=1200, temperature=0.0,
                  timeout=240, max_retries=1, insecure_tls=False, client=None):
    condition = "unified" if condition == "skill" else condition
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    client = client or SoCLaaSClient(timeout=timeout, max_retries=max_retries,
                                     insecure_tls=insecure_tls)
    provider = getattr(client, "provider", "unknown")
    instructions = instructions_for_condition(condition)
    prompts = prompt_manifest()
    instructions_hash = prompts["instruction_hashes"][condition]
    prior = _read_successful(output)
    records_by_id = {row["sample_id"]: row for row in records}
    compatible_conditions = {condition}
    if condition == "unified":
        compatible_conditions.add("skill")
    for sample_id, row in prior.items():
        if row.get("model") != client.model:
            raise ValueError(
                f"Cannot resume {output}: saved model {row.get('model')!r} differs "
                f"from current model {client.model!r}")
        if row.get("provider", "unknown") != provider:
            raise ValueError(f"Cannot resume {output}: provider has changed")
        if row.get("condition") not in compatible_conditions:
            raise ValueError(
                f"Cannot resume {output}: it contains condition {row.get('condition')!r}")
        if row.get("instructions_hash") != instructions_hash:
            raise ValueError(
                f"Cannot resume {output}: canonical instructions have changed")
        if row.get("skill_bundle_hash") != prompts["skill_bundle_hash"]:
            raise ValueError(
                f"Cannot resume {output}: canonical skill bundle has changed")
        current = records_by_id.get(sample_id)
        if current and row.get("evidence_hash") != current.get("evidence_hash"):
            raise ValueError(
                f"Cannot resume {output}: evidence changed for sample {sample_id}")
        if "temperature" in row and row["temperature"] != temperature:
            raise ValueError(
                f"Cannot resume {output}: temperature differs for sample {sample_id}")
        if ("max_output_tokens" in row
                and row["max_output_tokens"] != max_output_tokens):
            raise ValueError(
                f"Cannot resume {output}: output-token limit differs for sample {sample_id}")
    pending = [row for row in records if row["sample_id"] not in prior]
    limiter = RateLimiter(rpm)
    stop_event = threading.Event()
    write_lock = threading.Lock()
    completed_count = len(prior)
    error_count = 0
    api_call_count = int(status.state.get("api_calls", 0))
    total = len(records)
    status.update(phase=f"running_{condition}", condition=condition, total=total,
                  completed=completed_count, pending=len(pending), rpm=rpm,
                  api_calls=api_call_count, errors=0,
                  message="Using one fixed evidence manifest; no live retrieval calls.")
    print(f"[{condition}] starting: {len(pending)} pending, {completed_count}/{total} already complete",
          flush=True)

    def run_one(record):
        nonlocal completed_count, error_count, api_call_count
        base = {
            "sample_id": record["sample_id"], "index": record["index"],
            "condition": condition, "provider": provider, "model": client.model,
            "image_path": record["image_path"], "text": record["text"],
            "evidence_image_path": record.get("evidence_image_path"),
            "validation_index": record.get("validation_index"),
            "ground_truth_binary": record.get("ground_truth_binary"),
            "ground_truth_class": record.get("ground_truth_class"),
            "direct_evidence": record["direct_evidence"],
            "inverse_evidence": record["inverse_evidence"],
            "evidence_hash": record["evidence_hash"],
            "instructions_hash": instructions_hash,
            "skill_bundle_hash": prompts["skill_bundle_hash"],
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "error": None,
        }
        if stop_event.is_set():
            base["error"] = "stopped_after_call_timeout"
            with write_lock, output.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(base, ensure_ascii=False) + "\n")
            return base
        try:
            image = resolve_image(image_root, record["image_path"])
            limiter.acquire()
            started = time.monotonic()
            started_sgt = _sgt_now()
            with write_lock:
                api_call_count += 1
            status.update(current_sample=record["sample_id"], last_call_started_sgt=started_sgt)
            response = client.chat_completions_with_evidence(
                record["text"], str(image), evidence_block(record), instructions,
                temperature, max_output_tokens)
            duration = round(time.monotonic() - started, 3)
            base.update({
                "call_started_sgt": started_sgt,
                "call_duration_seconds": duration,
                "call_timed_out": duration > 300,
                "raw_response": client.text_from_chat_response(response),
                "api_response": response,
                "runtime_seconds": response.get("_runtime_seconds"),
                "usage": response.get("usage"),
            })
            base.update(parse_prediction(base["raw_response"]))
            if duration > 300:
                base["error"] = "call_exceeded_5_minutes"
                stop_event.set()
        except Exception as exc:
            base.update({"raw_response": "", "call_timed_out": False, "error": repr(exc)})
        with write_lock, output.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(base, ensure_ascii=False) + "\n")
        with write_lock:
            completed_count += 1
            if base.get("error"):
                error_count += 1
            status.update(completed=completed_count, pending=max(0, total - completed_count),
                          errors=error_count,
                          api_calls=api_call_count,
                          last_call_duration_seconds=base.get("call_duration_seconds", "-"),
                          message=("A call exceeded 5 minutes; stopping new API calls."
                                   if stop_event.is_set() else ""))
            if base.get("error"):
                outcome = f"ERROR {base['error']}"
            else:
                outcome = (f"{base.get('predicted_binary', 'unparsed')} / "
                           f"{base.get('predicted_class', 'unparsed')}")
            print(f"[{condition}] {completed_count}/{total} {record['sample_id']} "
                  f"{outcome} ({base.get('call_duration_seconds', '-') }s)", flush=True)
        return base

    results = []
    executor = ThreadPoolExecutor(max_workers=max(1, concurrency))
    futures = [executor.submit(run_one, record) for record in pending]
    try:
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result.get("error") == "call_exceeded_5_minutes":
                for other in futures:
                    other.cancel()
                break
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    status.update(phase=f"completed_{condition}", condition=condition, total=total,
                  completed=completed_count, pending=max(0, total - completed_count),
                  errors=error_count,
                  message=("Stopped because an API call exceeded 5 minutes."
                           if stop_event.is_set() else "Condition complete."))
    print(f"[{condition}] complete: {completed_count}/{total}, errors={error_count}", flush=True)
    return results
