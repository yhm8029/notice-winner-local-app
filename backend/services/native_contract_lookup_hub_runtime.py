from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path


def _load_hub_result_payload_text(text: str) -> list[dict] | None:
    out = str(text or "").strip()
    if not out:
        return None
    try:
        payload = json.loads(out)
    except Exception:
        start_obj = out.find("{")
        start_arr = out.find("[")
        starts = [pos for pos in (start_obj, start_arr) if pos >= 0]
        if not starts:
            return None
        start = min(starts)
        end = max(out.rfind("}"), out.rfind("]"))
        if end <= start:
            return None
        payload = json.loads(out[start : end + 1])
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    return None


def _get_hub_result_candidates_via_powershell(
    query: str,
    timeout_sec: float,
    *,
    helper_path: Path,
    max_results: int,
    normalize_candidates_fn: Callable[[object], list[dict]],
) -> list[dict] | None:
    query_value = str(query or "").strip()
    if not query_value or not helper_path.exists():
        return None
    query_b64 = base64.b64encode(query_value.encode("utf-8")).decode("ascii")
    for shell_cmd in ("powershell", "pwsh"):
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as temp_output:
                output_path = Path(temp_output.name)
            args = [
                shell_cmd,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(helper_path),
                "-QueryBase64",
                query_b64,
                "-OutputPath",
                str(output_path),
                "-MaxResults",
                str(max_results),
                "-TimeoutSec",
                str(float(timeout_sec)),
            ]
            proc = subprocess.run(
                subprocess.list2cmdline(args),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=max(10, int(timeout_sec) + 20),
                check=False,
            )
        except FileNotFoundError:
            continue
        except Exception:
            continue
        try:
            if proc.returncode != 0 or not output_path.exists():
                continue
            payload = _load_hub_result_payload_text(
                output_path.read_text(encoding="utf-8-sig", errors="ignore")
            )
            if payload is None:
                continue
            return normalize_candidates_fn(payload)
        finally:
            try:
                output_path.unlink(missing_ok=True)
            except Exception:
                pass
    return None
