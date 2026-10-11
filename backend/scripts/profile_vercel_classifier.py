"""Measure the local classifier workload against Vercel Function reference limits.

Run from the repository root:
    python backend\scripts\profile_vercel_classifier.py

This downloads and loads the configured classifier if it is not cached. It does
not load Gemma, call Gemini, make API/database requests, or run image OCR.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib import metadata
from pathlib import Path
from typing import Any

import psutil


VERCEL_REFERENCE = {
    "hobby_memory_mb": 2048,
    "python_function_bundle_mb": 500,
    "function_duration_seconds": 300,
}

SAMPLE_MESSAGES = (
    "Your account was locked. Verify your details immediately at https://example.com.",
    (
        "Hello, this is your bank's security team. We noticed unusual activity on "
        "your account. Please use the official app or call the number on your card "
        "to review recent transactions."
    ),
    (
        "Congratulations, you have been selected for a cash reward. Act now to "
        "claim your prize, confirm your banking information, and pay a small "
        "processing fee before this offer expires."
    ),
)

REQUIREMENTS_PATH = Path(__file__).resolve().parents[1] / "requirements.txt"


class PeakMemorySampler:
    def __init__(self, interval_seconds: float = 0.02) -> None:
        self.process = psutil.Process()
        self.interval_seconds = interval_seconds
        self.peak_rss_bytes = self.process.memory_info().rss
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                self.peak_rss_bytes = max(
                    self.peak_rss_bytes, self.process.memory_info().rss
                )
            except psutil.Error:
                pass
            self._stop.wait(self.interval_seconds)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()
        self.peak_rss_bytes = max(
            self.peak_rss_bytes, self.process.memory_info().rss
        )


def _bytes_to_mb(value: int) -> float:
    return round(value / (1024 * 1024), 2)


def _directory_size(path: Path) -> int:
    if not path.is_dir():
        return 0
    measured_files: set[Path] = set()
    total_bytes = 0
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        try:
            resolved_path = item.resolve(strict=True)
            if resolved_path not in measured_files:
                measured_files.add(resolved_path)
                total_bytes += resolved_path.stat().st_size
        except (OSError, RuntimeError):
            continue
    return total_bytes


def _classifier_cache_info() -> tuple[Path, int]:
    from huggingface_hub.constants import HF_HUB_CACHE

    repository_id = os.getenv(
        "LLM_MULTIHEAD_MODEL_ID", "ManokManokManok/bimBert_Scam-Detection"
    )
    repository_cache = Path(HF_HUB_CACHE) / f"models--{repository_id.replace('/', '--')}"
    snapshots = repository_cache / "snapshots"
    return snapshots, _directory_size(snapshots)


def _installed_backend_footprint() -> dict[str, Any]:
    """Estimate installed size for backend requirements and installed dependencies."""
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    distributions = {
        canonicalize_name(dist.metadata["Name"]): dist
        for dist in metadata.distributions()
        if dist.metadata.get("Name")
    }
    pending: list[str] = []
    missing: set[str] = set()

    for raw_line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines():
        requirement_text = raw_line.split("#", 1)[0].strip()
        if requirement_text:
            pending.append(canonicalize_name(Requirement(requirement_text).name))

    included: set[str] = set()
    while pending:
        package_name = pending.pop()
        if package_name in included:
            continue
        distribution = distributions.get(package_name)
        if distribution is None:
            missing.add(package_name)
            continue
        included.add(package_name)
        for raw_dependency in distribution.requires or ():
            dependency = Requirement(raw_dependency)
            if dependency.marker is None or dependency.marker.evaluate():
                pending.append(canonicalize_name(dependency.name))

    measured_files: set[Path] = set()
    total_bytes = 0
    package_sizes: list[tuple[str, int]] = []
    for package_name in sorted(included):
        distribution = distributions[package_name]
        package_bytes = 0
        for relative_path in distribution.files or ():
            file_path = Path(distribution.locate_file(relative_path))
            try:
                resolved_path = file_path.resolve(strict=True)
                if resolved_path.is_file() and resolved_path not in measured_files:
                    size = resolved_path.stat().st_size
                    measured_files.add(resolved_path)
                    total_bytes += size
                    package_bytes += size
            except (OSError, RuntimeError):
                continue
        package_sizes.append((package_name, package_bytes))

    largest_packages = sorted(package_sizes, key=lambda item: item[1], reverse=True)[:8]
    return {
        "estimated_installed_bytes": total_bytes,
        "distribution_count": len(included),
        "missing_distributions": sorted(missing),
        "largest_distributions": [
            {"name": name, "mb": _bytes_to_mb(size)}
            for name, size in largest_packages
        ],
    }


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _benchmark_inference(
    detector: Any, iterations: int, concurrency: int
) -> dict[str, Any]:
    def infer(index: int) -> tuple[float, dict[str, Any]]:
        message = SAMPLE_MESSAGES[index % len(SAMPLE_MESSAGES)]
        started = time.perf_counter()
        result = detector.detect(message)
        return time.perf_counter() - started, result

    for index in range(min(3, iterations)):
        infer(index)

    started = time.perf_counter()
    latencies: list[float] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(infer, index)
            for index in range(iterations)
        ]
        for future in as_completed(futures):
            latency, result = future.result()
            if not isinstance(result.get("is_scam"), bool):
                raise RuntimeError("Classifier returned an unexpected result")
            latencies.append(latency)
    elapsed = time.perf_counter() - started

    return {
        "requests": iterations,
        "concurrency": concurrency,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_requests_per_second": round(iterations / elapsed, 2),
        "latency_ms": {
            "p50": round(_percentile(latencies, 0.50) * 1000, 2),
            "p95": round(_percentile(latencies, 0.95) * 1000, 2),
            "max": round(max(latencies) * 1000, 2),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load and benchmark the real local scam classifier. "
            "Gemma is never loaded by this script."
        )
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of measured classifications (default: 20)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Maximum simultaneous classifier calls (default: 2)",
    )
    parser.add_argument(
        "--memory-budget-mb",
        type=int,
        default=VERCEL_REFERENCE["hobby_memory_mb"],
        help="Memory comparison budget in MiB (default: Vercel Hobby reference, 2048)",
    )
    parser.add_argument(
        "--bundle-budget-mb",
        type=int,
        default=VERCEL_REFERENCE["python_function_bundle_mb"],
        help="Bundle comparison budget in MiB (default: Python Function reference, 500)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path for saving the complete JSON report",
    )
    args = parser.parse_args()
    if args.iterations < 1 or args.concurrency < 1:
        parser.error("--iterations and --concurrency must be positive")
    if args.memory_budget_mb < 1 or args.bundle_budget_mb < 1:
        parser.error("memory and bundle budgets must be positive")
    return args


def main() -> int:
    args = _parse_args()
    backend_dir = str(REQUIREMENTS_PATH.parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from dotenv import load_dotenv

    load_dotenv(REQUIREMENTS_PATH.parent / ".env")

    process = psutil.Process()
    initial_rss_bytes = process.memory_info().rss
    host_memory = psutil.virtual_memory()
    cache_snapshots, cache_before_bytes = _classifier_cache_info()
    sampler = PeakMemorySampler()
    sampler.start()
    load_started = time.perf_counter()

    try:
        from src.infrastructure.ai.loaders import load_multihead_model
        from src.use_cases.ai.scam_detection import ScamDetectionUseCase

        tokenizer, model, scam_types = load_multihead_model()
        model_load_seconds = time.perf_counter() - load_started
        detector = ScamDetectionUseCase(tokenizer, model, scam_types)
        benchmark = _benchmark_inference(
            detector, args.iterations, args.concurrency
        )
        try:
            import torch

            torch_threads = torch.get_num_threads()
        except ImportError:
            torch_threads = None
        parameter_count = sum(
            parameter.numel() for parameter in model.parameters()
        )
    finally:
        sampler.stop()

    cache_after_bytes = _directory_size(cache_snapshots)
    package_footprint = _installed_backend_footprint()
    peak_rss_mb = _bytes_to_mb(sampler.peak_rss_bytes)
    package_footprint_mb = _bytes_to_mb(
        package_footprint["estimated_installed_bytes"]
    )
    memory_budget_mb = args.memory_budget_mb
    bundle_budget_mb = args.bundle_budget_mb
    warnings = []

    if peak_rss_mb > memory_budget_mb * 0.75:
        warnings.append(
            "Peak process RSS exceeds 75% of the selected memory budget; "
            "leave more headroom for the function runtime and request overhead."
        )
    if package_footprint_mb > bundle_budget_mb:
        warnings.append(
            "Estimated installed backend package footprint exceeds the selected "
            "bundle budget. This estimate is not Vercel's final deployment bundle size."
        )
    if model_load_seconds > VERCEL_REFERENCE["function_duration_seconds"]:
        warnings.append(
            "Model load exceeded the 300-second Vercel Function duration reference."
        )
    if package_footprint["missing_distributions"]:
        warnings.append(
            "Some backend requirement distributions are not installed locally; "
            "the package footprint estimate is incomplete."
        )

    likely_exceeds = (
        peak_rss_mb > memory_budget_mb
        or package_footprint_mb > bundle_budget_mb
        or model_load_seconds > VERCEL_REFERENCE["function_duration_seconds"]
    )
    report = {
        "scope": (
            "Classifier load and text inference only; no Gemma, Gemini, Django "
            "HTTP request, database, or image OCR."
        ),
        "verdict": (
            "likely_exceeds_reference_budgets"
            if likely_exceeds
            else "within_raw_reference_budgets_locally"
        ),
        "limits": {
            "memory_budget_mb": memory_budget_mb,
            "python_function_bundle_budget_mb": bundle_budget_mb,
            "function_duration_reference_seconds": VERCEL_REFERENCE[
                "function_duration_seconds"
            ],
            "memory_comparison_source": "Vercel Hobby Function reference",
            "bundle_comparison_source": "Vercel Python Function reference",
        },
        "host": {
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "physical_memory_mb": _bytes_to_mb(host_memory.total),
            "available_memory_before_load_mb": _bytes_to_mb(host_memory.available),
            "torch_threads": torch_threads,
        },
        "classifier": {
            "model_id": os.getenv(
                "LLM_MULTIHEAD_MODEL_ID",
                "ManokManokManok/bimBert_Scam-Detection",
            ),
            "scam_type_count": len(scam_types),
            "parameter_count": parameter_count,
            "load_seconds_including_first_download": round(model_load_seconds, 2),
            "cached_classifier_files_mb": _bytes_to_mb(cache_after_bytes),
            "cache_bytes_added_this_run_mb": _bytes_to_mb(
                max(0, cache_after_bytes - cache_before_bytes)
            ),
            "process_rss_before_load_mb": _bytes_to_mb(initial_rss_bytes),
            "process_peak_rss_mb": peak_rss_mb,
            "process_rss_increase_mb": _bytes_to_mb(
                max(0, sampler.peak_rss_bytes - initial_rss_bytes)
            ),
        },
        "inference": benchmark,
        "backend_packages": {
            "estimated_installed_footprint_mb": package_footprint_mb,
            "distribution_count": package_footprint["distribution_count"],
            "missing_distributions": package_footprint["missing_distributions"],
            "largest_distributions": package_footprint["largest_distributions"],
            "note": (
                "Local installed-package estimate, not an exact Vercel bundle "
                "measurement; Vercel's build platform, OS, and architecture differ."
            ),
        },
        "warnings": warnings,
        "interpretation": (
            "A local pass is a sizing signal, not a Vercel compatibility guarantee. "
            "Vercel uses ephemeral, autoscaled Functions; first-load downloads, "
            "cold starts, simultaneous instances, deployed bundle size, and API "
            "features outside this benchmark still need validation on Vercel."
        ),
    }

    report_json = json.dumps(report, indent=2)
    print(report_json)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(report_json + "\n", encoding="utf-8")
        print(f"\nReport saved to {args.json_out}")

    return 2 if likely_exceeds else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "verdict": "benchmark_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "hint": (
                        "Run from the repository root with the backend "
                        "requirements installed and network access to Hugging Face."
                    ),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
