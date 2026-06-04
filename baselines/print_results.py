#!/usr/bin/env python3
"""
Summarize Quokka result JSON files using repo-local baseline data.

Usage:
  python baselines/print_results.py path/to/run.json
  python baselines/print_results.py baselines/results
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


RESULT_SUFFIX = "_invariant_generation_results.json"
SOLVED_RESULTS = {"TRUE", "FALSE"}
PRINT_RESULT_ORDER = ["TRUE", "FALSE", "UNKNOWN", "TIMEOUT"]
ASSERT_RESULT_ORDER = ["TRUE", "FALSE", "UNKNOWN", "TIMEOUT", "KILLED", "MISSING"]

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results"
DEFAULT_BASELINES = {
    "uautomizer": REPO_ROOT / "Dataset" / "timing_uautomizer.json",
    "esbmc": REPO_ROOT / "Dataset" / "timing_esbmc.json",
}


@dataclass
class RunSummary:
    label: str
    path: Path
    verifier: str
    baseline_path: Path
    total_problems: int
    total_samples: int
    correct_problem_count: int
    false_problem_count: int
    timeout_problem_count: int
    representative_result_counts: Dict[str, int]
    assert_result_counts: Dict[str, int]
    consistent_problem_count: int
    fallback_problem_count: int
    faster_problem_count: int
    geometric_mean_speedup: float
    faster_only_geometric_mean_speedup: float
    speedups_raw: List[float]
    correct_results: Dict[str, Dict[str, Any]]


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse JSON in {path}: {exc}")


def canonical_result(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if value is None:
        return "UNKNOWN"
    result = str(value).strip().upper()
    if result == "ERROR":
        return "UNKNOWN"
    return result or "UNKNOWN"


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_verifier(path: Path, override: str) -> str:
    if override != "auto":
        return override
    match = re.search(r"verifier=([A-Za-z0-9_-]+)", path.name)
    if match:
        verifier = match.group(1).lower()
        if verifier in DEFAULT_BASELINES:
            return verifier
    return "uautomizer"


def parse_model_label(path: Path) -> str:
    name = path.name
    if name.endswith(RESULT_SUFFIX):
        name = name[: -len(RESULT_SUFFIX)]
    match = re.match(
        r"(?P<model>.+?)_cot=(?P<cot>True|False)_best_of_n=(?P<best_of_n>\d+)"
        r"_num_shots=(?P<num_shots>\d+)_temperature=(?P<temperature>[\d.]+)"
        r"_verifier=(?P<verifier>[A-Za-z0-9_-]+)$",
        name,
    )
    if not match:
        return name

    model = match.group("model")
    extras: List[str] = []
    if match.group("cot") == "True":
        extras.append("CoT")
    if match.group("best_of_n") != "1":
        extras.append(f"n={match.group('best_of_n')}")
    if match.group("num_shots") != "0":
        extras.append(f"{match.group('num_shots')}-shot")
    if match.group("temperature") != "0.0":
        extras.append(f"t={match.group('temperature')}")
    if match.group("verifier") != "uautomizer":
        extras.append(match.group("verifier"))
    if extras:
        return f"{model} ({', '.join(extras)})"
    return model


def load_baseline_lookup(path: Path) -> Dict[str, Dict[str, Any]]:
    data = load_json(path)
    if not isinstance(data, list):
        raise SystemExit(f"Expected baseline JSON list in {path}")

    lookup: Dict[str, Dict[str, Any]] = {}
    for entry in data:
        filename = entry.get("filename")
        if not filename:
            continue
        lookup[filename] = {
            "filename": filename,
            "result": canonical_result(entry.get("result")),
            "time_taken": to_float(entry.get("time_taken")),
        }
    return lookup


def aggregate_raw_sample_result(sample: Dict[str, Any]) -> Optional[str]:
    assume_result = sample.get("assume_verification_result")
    assert_result = sample.get("assert_verification_result")
    if assume_result is None or assert_result is None:
        return None

    assume_value = canonical_result(assume_result.get("result"))
    assert_value = canonical_result(assert_result.get("result"))

    if assume_value == "KILLED" or assert_value == "KILLED":
        return "UNKNOWN"
    if assume_value == "FALSE":
        return "FALSE"
    if assume_value == "TRUE" and assert_value == "TRUE":
        return "TRUE"
    if assert_value == "FALSE":
        return "UNKNOWN"
    if assume_value == "TIMEOUT" or assert_value == "TIMEOUT":
        return "TIMEOUT"
    return "UNKNOWN"


def sample_total_time(sample: Dict[str, Any]) -> float:
    generation_time = to_float(sample.get("generation_time")) or 0.0
    assume_time = to_float(sample.get("assume_verification_time")) or 0.0
    assert_time = to_float(sample.get("assert_verification_time")) or 0.0
    verify_time_taken = to_float(sample.get("verify_time_taken")) or 0.0

    assume_result = sample.get("assume_verification_result")
    assert_result = sample.get("assert_verification_result")

    if assume_time == 0.0 and assert_time == 0.0:
        return generation_time + verify_time_taken

    if (
        assume_result is not None
        and canonical_result(assume_result.get("result")) == "FALSE"
        and (
            assert_result is None
            or canonical_result(assert_result.get("result")) == "KILLED"
            or assume_time <= assert_time
        )
    ):
        return generation_time + assume_time

    return generation_time + max(assume_time, assert_time)


def geometric_mean(values: Sequence[float]) -> float:
    if not values:
        return 1.0
    return math.exp(sum(math.log(value) for value in values) / len(values))


def format_fraction(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0/0 (0.0%)"
    pct = numerator / denominator * 100.0
    return f"{numerator}/{denominator} ({pct:.1f}%)"


def format_count_map(counts: Dict[str, int], order: Sequence[str], denominator: int) -> str:
    parts = []
    for key in order:
        value = counts.get(key, 0)
        pct = (value / denominator * 100.0) if denominator else 0.0
        parts.append(f"{key}={value} ({pct:.1f}%)")
    return ", ".join(parts)


def format_speedup_thresholds(speedups_raw: Sequence[float]) -> str:
    thresholds = [
        (">1.0", lambda value: value > 1.0),
        ("≥1.2", lambda value: value >= 1.2),
        ("≥1.5", lambda value: value >= 1.5),
        ("≥2.0", lambda value: value >= 2.0),
    ]
    total = len(speedups_raw)
    parts = []
    for label, predicate in thresholds:
        count = sum(1 for value in speedups_raw if predicate(value))
        pct = (count / total * 100.0) if total else 0.0
        parts.append(f"{label}: {count}/{total} ({pct:.1f}%)")
    return ", ".join(parts)


def format_timeout_label(timeout: float) -> str:
    return f"{int(timeout)}s" if int(timeout) == timeout else f"{timeout:g}s"


def build_correct_results(results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """Replicate compare_models.py semantics.

    A problem counts as solved by the model iff at least one sample has
    assert_verification_result.result == TRUE. The time for that problem is the
    minimum total time across such samples.
    """
    solved_results: Dict[str, Dict[str, Any]] = {}
    for filename, samples in results.items():
        best_time = None
        for sample in samples:
            assert_result = canonical_result(
                (sample.get("assert_verification_result") or {}).get("result")
            )
            if assert_result != "TRUE":
                continue
            sample_time = sample_total_time(sample)
            if best_time is None or sample_time < best_time:
                best_time = sample_time

        if best_time is not None:
            solved_results[filename] = {
                "filename": filename,
                "result": "TRUE",
                "time_taken": best_time,
            }
        else:
            solved_results[filename] = {
                "filename": filename,
                "result": "UNKNOWN",
                "time_taken": None,
            }
    return solved_results


def solved_within_timeout(
    results: Dict[str, Dict[str, Any]], timeout: float
) -> Dict[str, float]:
    solved = {}
    for filename, entry in results.items():
        result_value = canonical_result(entry.get("result"))
        time_taken = to_float(entry.get("time_taken"))
        if result_value in SOLVED_RESULTS and time_taken is not None and time_taken <= timeout:
            solved[filename] = time_taken
    return solved


def ensure_results_mapping(data: Any, path: Path) -> Dict[str, List[Dict[str, Any]]]:
    if not isinstance(data, dict):
        raise SystemExit(
            f"Expected Quokka result JSON in {path} to be a dict of filename -> sample list."
        )

    normalized: Dict[str, List[Dict[str, Any]]] = {}
    for filename, samples in data.items():
        if isinstance(samples, list):
            normalized[filename] = [sample for sample in samples if isinstance(sample, dict)]
        else:
            raise SystemExit(f"Expected sample list for {filename} in {path}")
    return normalized


def summarize_run(path: Path, baseline_override: Optional[Path], verifier_override: str) -> RunSummary:
    verifier = infer_verifier(path, verifier_override)
    baseline_path = baseline_override or DEFAULT_BASELINES[verifier]
    baseline_lookup = load_baseline_lookup(baseline_path)
    results = ensure_results_mapping(load_json(path), path)

    missing = sorted(set(results) - set(baseline_lookup))
    if missing:
        preview = ", ".join(missing[:5])
        suffix = "" if len(missing) <= 5 else f", ... ({len(missing)} missing)"
        raise SystemExit(
            f"Results in {path} reference files not found in {baseline_path}: {preview}{suffix}"
        )

    representative_result_counts = {key: 0 for key in PRINT_RESULT_ORDER}
    assert_result_counts = {key: 0 for key in ASSERT_RESULT_ORDER}
    speedups = []
    faster_only_speedups = []
    speedups_raw = []
    correct_problem_count = 0
    false_problem_count = 0
    timeout_problem_count = 0
    consistent_problem_count = 0
    fallback_problem_count = 0
    faster_problem_count = 0
    total_samples = 0

    for filename, samples in sorted(results.items()):
        baseline_entry = baseline_lookup[filename]
        baseline_result = baseline_entry["result"]
        baseline_time = baseline_entry["time_taken"]

        total_samples += len(samples)

        if any(
            canonical_result((sample.get("assert_verification_result") or {}).get("result")) == "TRUE"
            for sample in samples
        ):
            correct_problem_count += 1
        if any(
            canonical_result((sample.get("assert_verification_result") or {}).get("result")) == "FALSE"
            for sample in samples
        ):
            false_problem_count += 1
        if any(
            canonical_result((sample.get("assume_verification_result") or {}).get("result")) == "TIMEOUT"
            or canonical_result((sample.get("assert_verification_result") or {}).get("result")) == "TIMEOUT"
            for sample in samples
        ):
            timeout_problem_count += 1

        for sample in samples:
            assert_result = sample.get("assert_verification_result")
            assert_key = (
                canonical_result(assert_result.get("result"))
                if assert_result is not None
                else "MISSING"
            )
            if assert_key not in assert_result_counts:
                assert_result_counts[assert_key] = 0
            assert_result_counts[assert_key] += 1

        consistent_samples = [
            sample
            for sample in samples
            if canonical_result(sample.get("result")) == baseline_result
        ]
        representative = min(
            consistent_samples or samples,
            key=sample_total_time,
        )
        representative_result = canonical_result(representative.get("result"))
        representative_result_counts.setdefault(representative_result, 0)
        representative_result_counts[representative_result] += 1

        raw_representative_result = aggregate_raw_sample_result(representative)
        if representative_result == baseline_result:
            consistent_problem_count += 1
            if raw_representative_result not in SOLVED_RESULTS:
                fallback_problem_count += 1

        verified_consistent_samples = [
            sample
            for sample in samples
            if canonical_result(sample.get("result")) == baseline_result
            and canonical_result((sample.get("assert_verification_result") or {}).get("result")) == "TRUE"
        ]

        if verified_consistent_samples and baseline_time and baseline_time > 0:
            best_verified_sample = min(verified_consistent_samples, key=sample_total_time)
            verified_time = sample_total_time(best_verified_sample)
            raw_speedup = baseline_time / verified_time if verified_time > 0 else 1.0
            capped_speedup = max(raw_speedup, 1.0)
            if raw_speedup > 1.0:
                faster_problem_count += 1
                faster_only_speedups.append(capped_speedup)
            speedups.append(capped_speedup)
            speedups_raw.append(raw_speedup)
        else:
            speedups.append(1.0)
            speedups_raw.append(1.0)

    correct_results = build_correct_results(results)

    return RunSummary(
        label=parse_model_label(path),
        path=path,
        verifier=verifier,
        baseline_path=baseline_path,
        total_problems=len(results),
        total_samples=total_samples,
        correct_problem_count=correct_problem_count,
        false_problem_count=false_problem_count,
        timeout_problem_count=timeout_problem_count,
        representative_result_counts=representative_result_counts,
        assert_result_counts=assert_result_counts,
        consistent_problem_count=consistent_problem_count,
        fallback_problem_count=fallback_problem_count,
        faster_problem_count=faster_problem_count,
        geometric_mean_speedup=geometric_mean(speedups),
        faster_only_geometric_mean_speedup=geometric_mean(faster_only_speedups),
        speedups_raw=speedups_raw,
        correct_results=correct_results,
    )


def print_single_run(summary: RunSummary) -> None:
    print(f"Run: {summary.path}")
    print(f"Label: {summary.label}")
    print(f"Verifier baseline: {summary.baseline_path}")
    print(f"Problems: {summary.total_problems}")
    print(f"Samples: {summary.total_samples}")
    print()
    print("Synthesized invariants")
    print(
        "  Problems with at least one verifier-confirmed invariant "
        f"(assert=TRUE): {format_fraction(summary.correct_problem_count, summary.total_problems)}"
    )
    print(
        "  Problems with at least one verifier-rejected invariant "
        f"(assert=FALSE): {format_fraction(summary.false_problem_count, summary.total_problems)}"
    )
    print(
        "  Problems with any assume/assert timeout: "
        f"{format_fraction(summary.timeout_problem_count, summary.total_problems)}"
    )
    print(
        "  Sample assert-result distribution: "
        f"{format_count_map(summary.assert_result_counts, ASSERT_RESULT_ORDER, summary.total_samples)}"
    )
    print()
    print("Best-of-N outcomes")
    print(
        "  Representative result distribution: "
        f"{format_count_map(summary.representative_result_counts, PRINT_RESULT_ORDER, summary.total_problems)}"
    )
    print(
        "  Problems consistent with the baseline: "
        f"{format_fraction(summary.consistent_problem_count, summary.total_problems)}"
    )
    print(
        "  Consistent problems using baseline fallback "
        "(raw assume/assert result not definitive): "
        f"{format_fraction(summary.fallback_problem_count, summary.total_problems)}"
    )
    print()
    print("Speedup vs baseline")
    print(
        "  Geometric mean speedup: "
        f"{summary.geometric_mean_speedup:.3f}x"
    )
    print(
        "  Geometric mean speedup on faster verified samples only: "
        f"{summary.faster_only_geometric_mean_speedup:.3f}x"
    )
    print(
        "  Problems with verified speedup >1.0x: "
        f"{format_fraction(summary.faster_problem_count, summary.total_problems)}"
    )
    print(
        "  Verified speedup thresholds: "
        f"{format_speedup_thresholds(summary.speedups_raw)}"
    )
    print()
    print(
        "Note: speedup only credits samples whose top-level result matches the baseline and "
        "whose assert check returned TRUE. Final top-level results may still match the baseline "
        "via Quokka's fallback when assume/assert returns UNKNOWN or TIMEOUT."
    )


def format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def format_row(row: Sequence[str]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    lines = [format_row(headers), format_row(["-" * width for width in widths])]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)


def compare_model_rows(
    summaries: Sequence[RunSummary], timeouts: Sequence[float]
) -> tuple[int, str, List[List[str]]]:
    if not summaries:
        return 0, "baseline", []

    baseline_lookup = load_baseline_lookup(summaries[0].baseline_path)
    total_instances = len(baseline_lookup)
    baseline_solved_sets = {
        timeout: solved_within_timeout(baseline_lookup, timeout) for timeout in timeouts
    }
    baseline_label = summaries[0].baseline_path.stem

    rows: List[List[str]] = []
    for summary in sorted(summaries, key=lambda item: (item.correct_problem_count, item.label)):
        row = [summary.label, str(summary.correct_problem_count)]
        model_solved_sets = {
            timeout: solved_within_timeout(summary.correct_results, timeout)
            for timeout in timeouts
        }
        for timeout in timeouts:
            solved = model_solved_sets[timeout]
            baseline_solved = baseline_solved_sets[timeout]
            extra = len(set(solved) - set(baseline_solved))
            solved_count = len(solved)
            unsolved_count = total_instances - solved_count
            solved_time_sum = sum(solved.values())
            par = (
                (solved_time_sum + unsolved_count * timeout) / total_instances
                if total_instances
                else 0.0
            )
            row.extend([str(extra), str(solved_count), f"{par:.1f}"])
        rows.append(row)

    return total_instances, baseline_label, rows


def print_compare_models_summary(summaries: Sequence[RunSummary], timeouts: Sequence[float]) -> None:
    total_instances, baseline_label, rows = compare_model_rows(summaries, timeouts)
    headers = ["Model", "#Corr"]
    for timeout in timeouts:
        label = format_timeout_label(timeout)
        headers.extend([f"#Ext@{label}", f"#Slv@{label}", f"PAR@{label}"])

    print(f"Total instances ({baseline_label}): {total_instances}")
    print()
    print(format_table(headers, rows))


def extension_cases_at_timeout(
    correct_results: Dict[str, Dict[str, Any]],
    baseline_lookup: Dict[str, Dict[str, Any]],
    timeout: float,
) -> List[tuple[str, Optional[float], float]]:
    baseline_solved = solved_within_timeout(baseline_lookup, timeout)
    model_solved = solved_within_timeout(correct_results, timeout)
    cases: List[tuple[str, Optional[float], float]] = []
    for filename in sorted(set(model_solved) - set(baseline_solved)):
        baseline_time = to_float(baseline_lookup[filename].get("time_taken"))
        cases.append((filename, baseline_time, model_solved[filename]))
    return cases


def print_extension_case_lists(
    summaries: Sequence[RunSummary], timeouts: Sequence[float]
) -> None:
    if not summaries:
        return

    baseline_lookup = load_baseline_lookup(summaries[0].baseline_path)
    print()
    print("Extension cases (#Ext@T: model solved within T, baseline not)")
    for summary in summaries:
        print()
        print(f"  {summary.label} ({summary.path.name})")
        for timeout in timeouts:
            label = format_timeout_label(timeout)
            cases = extension_cases_at_timeout(
                summary.correct_results, baseline_lookup, timeout
            )
            print(f"    #Ext@{label}: {len(cases)}")
            for filename, baseline_time, model_time in cases:
                baseline_display = (
                    f"{baseline_time:.1f}s"
                    if baseline_time is not None
                    else "n/a"
                )
                print(
                    f"      {filename}  baseline={baseline_display}  "
                    f"model={model_time:.1f}s"
                )


def print_compare_models_latex(
    summaries: Sequence[RunSummary],
    timeouts: Sequence[float],
    caption: str,
    label: str,
) -> None:
    total_instances, _, rows = compare_model_rows(summaries, timeouts)
    _ = total_instances

    print()
    print("\\begin{table*}[!tb]")
    print("  \\centering")
    print("  \\scriptsize")
    print("  \\renewcommand{\\arraystretch}{1.2}")
    print("  \\setlength{\\tabcolsep}{2pt}")
    col_spec = "p{4.5cm}r" + ("ccc" * len(timeouts))
    print(f"  \\begin{{tabular}}{{{col_spec}}}")
    print("    \\toprule")

    top = "    \\multirow{2}{*}{\\textbf{Model}} & \\multirow{2}{*}{\\textbf{\\#Corr.}}"
    for timeout in timeouts:
        top += f" & \\multicolumn{{3}}{{c}}{{\\textbf{{{format_timeout_label(timeout)}}}}}"
    top += " \\\\"
    print(top)

    cmidrule = "   "
    col = 3
    for _ in timeouts:
        cmidrule += f" \\cmidrule(lr){{{col}-{col + 2}}}"
        col += 3
    print(cmidrule)

    sub = "    &"
    for _ in timeouts:
        sub += " & \\#Ext & \\#Slv & $\\bar{T}$"
    sub += " \\\\"
    print(sub)
    print("    \\midrule")

    for row in rows:
        latex_row = "    " + " & ".join(row) + " \\\\"
        print(latex_row)

    print("    \\bottomrule")
    print("  \\end{tabular}")
    print(f"  \\caption{{{caption}}}")
    print(f"  \\label{{{label}}}")
    print("\\end{table*}")


def collect_result_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise SystemExit(f"Path does not exist: {path}")

    files = sorted(path.glob(f"*{RESULT_SUFFIX}"))
    if files:
        return files

    files = sorted(candidate for candidate in path.glob("*.json") if candidate.is_file())
    if not files:
        raise SystemExit(f"No JSON result files found in {path}")
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize Quokka result JSON files using compare_models-style metrics."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(DEFAULT_RESULTS_DIR),
        help="Result JSON file or directory of result JSON files (default: baselines/results).",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Override the baseline JSON path. By default this uses Dataset/timing_<verifier>.json.",
    )
    parser.add_argument(
        "--verifier",
        choices=["auto", "uautomizer", "esbmc"],
        default="auto",
        help="Baseline verifier to use when it cannot be inferred from the result filename.",
    )
    parser.add_argument(
        "--timeouts",
        type=float,
        nargs="+",
        default=[30, 500],
        help="Timeout thresholds used for #Extra, #Solved, and PAR reporting.",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Also print the single-run diagnostic summary for each result file.",
    )
    parser.add_argument(
        "--latex",
        action="store_true",
        help="Also print a LaTeX table with the compare_models-style summary.",
    )
    parser.add_argument(
        "--list-ext",
        action="store_true",
        help="List benchmark filenames counted in #Ext@T for each result file.",
    )
    parser.add_argument(
        "--caption",
        type=str,
        default=(
            "Model comparison: correct invariants, extra solved instances over the baseline, "
            "and PAR time."
        ),
        help="Caption used with --latex.",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="tab:model_comparison",
        help="LaTeX label used with --latex.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.path).resolve()
    baseline_override = Path(args.baseline).resolve() if args.baseline else None
    timeouts = sorted(args.timeouts)
    result_files = collect_result_files(path)
    summaries = [
        summarize_run(result_file, baseline_override, args.verifier)
        for result_file in result_files
    ]

    print_compare_models_summary(summaries, timeouts)

    if args.list_ext:
        print_extension_case_lists(summaries, timeouts)

    if args.latex:
        print_compare_models_latex(summaries, timeouts, args.caption, args.label)

    if args.detailed:
        for index, summary in enumerate(summaries):
            print()
            if index > 0:
                print("=" * 80)
                print()
            print_single_run(summary)


if __name__ == "__main__":
    main()
