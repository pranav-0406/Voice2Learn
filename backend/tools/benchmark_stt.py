"""Benchmark faster-whisper configurations on the same local recordings.

Example:
    python tools/benchmark_stt.py recordings/*.wav --warmup 1 --runs 3

The script prints JSON only. It never uploads audio or logs transcript text.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("recordings", nargs="+", type=Path)
    parser.add_argument("--models", nargs="+", default=["tiny", "base", "small"])
    parser.add_argument("--devices", nargs="+", default=["cpu", "cuda"])
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise SystemExit("Install backend/requirements-stt.txt first.") from error

    results: list[dict[str, object]] = []
    for model_name in args.models:
        for device in args.devices:
            compute_type = "float16" if device == "cuda" else "int8"
            load_started = time.perf_counter()
            try:
                model = WhisperModel(model_name, device=device, compute_type=compute_type)
            except Exception as error:
                results.append({
                    "model": model_name,
                    "device": device,
                    "compute_type": compute_type,
                    "status": "unavailable",
                    "error_type": type(error).__name__,
                })
                continue
            load_ms = (time.perf_counter() - load_started) * 1000
            samples: list[float] = []
            failure_type: str | None = None
            for recording in args.recordings:
                for run in range(args.warmup + args.runs):
                    started = time.perf_counter()
                    try:
                        segments, info = model.transcribe(
                            str(recording),
                            beam_size=1,
                            vad_filter=True,
                            condition_on_previous_text=False,
                        )
                        " ".join(segment.text.strip() for segment in segments if segment.text.strip())
                    except Exception as error:
                        failure_type = type(error).__name__
                        break
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    if run >= args.warmup:
                        samples.append(elapsed_ms)
                if failure_type:
                    break
            results.append({
                "model": model_name,
                "device": device,
                "compute_type": compute_type,
                "status": "ok" if not failure_type else "inference_unavailable",
                "cold_load_ms": round(load_ms, 1),
                "warm_runs": len(samples),
                "mean_transcription_ms": round(sum(samples) / len(samples), 1) if samples else None,
                "min_transcription_ms": round(min(samples), 1) if samples else None,
                "recording_count": len(args.recordings),
                "error_type": failure_type,
                "note": "Transcript text intentionally omitted; compare quality separately.",
            })
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
