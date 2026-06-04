#!/usr/bin/env python3
"""Analyze Quokka benchmark results with audited helper metrics.

Uses the same E2E timing and #Ext@T semantics as baselines/print_results.py.

Categories (mutually exclusive per benchmark):
  solved_and_faster       assert=TRUE and fastest-correct E2E < tolerance * baseline time
  semantic_extension      assert=TRUE but baseline result is not TRUE (audited; not #Ext@T)
  correct_but_slower      assert=TRUE, baseline TRUE, verifier-confirmed path slower
  correct_no_effect       assert=TRUE, baseline TRUE, timing within tolerance band
  faster_but_not_solved   raw E2E faster but no assert=TRUE (NOT an improvement)
  regression              baseline result TRUE but no assert=TRUE sample
  both_false_or_incomparable  otherwise

Official #Ext@T counts are reported separately (model solved within T, baseline not).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "baselines"))

from print_results import (  # noqa: E402
    DEFAULT_BASELINES,
    build_correct_results,
    canonical_result,
    load_baseline_lookup,
    sample_total_time,
    solved_within_timeout,
    to_float,
)


def load_results(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected dict of filename -> samples in {path}")
    return {
        filename: [sample for sample in samples if isinstance(sample, dict)]
        for filename, samples in data.items()
        if isinstance(samples, list)
    }


def baseline_entry_for_lookup(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "filename": entry["filename"],
        "result": entry["result"],
        "time_taken": entry["time_taken"],
    }


def model_solved_at(
    correct_results: Dict[str, Dict[str, Any]], filename: str, timeout: float
) -> bool:
    solved = solved_within_timeout(correct_results, timeout)
    return filename in solved


def baseline_solved_at(
    baseline_lookup: Dict[str, Dict[str, Any]], filename: str, timeout: float
) -> bool:
    entry = baseline_lookup.get(filename)
    if not entry:
        return False
    solved = solved_within_timeout({filename: baseline_entry_for_lookup(entry)}, timeout)
    return filename in solved


def analyze(
    results_path: Path,
    baseline_path: Path,
    tolerance: float = 0.95,
    timeouts: Optional[List[float]] = None,
) -> dict:
    if timeouts is None:
        timeouts = [30.0, 500.0]

    results = load_results(results_path)
    baseline_lookup = load_baseline_lookup(baseline_path)
    correct_results = build_correct_results(results)

    rows: List[dict] = []
    total_extracted = 0
    total_assume_true = 0
    total_assert_true = 0
    total_samples = 0
    corr_benchmarks = 0

    for fname in sorted(results.keys()):
        base = baseline_lookup.get(fname, {})
        bt = to_float(base.get("time_taken")) or 0.0
        br = canonical_result(base.get("result"))

        samples = results[fname]
        if not samples:
            continue

        for sample in samples:
            total_samples += 1
            inv_count = sample.get("invariants_count") or 0
            response = (sample.get("model_response") or "").strip()
            if inv_count > 0 or response:
                total_extracted += 1
            assume_r = canonical_result(
                (sample.get("assume_verification_result") or {}).get("result")
            )
            assert_r = canonical_result(
                (sample.get("assert_verification_result") or {}).get("result")
            )
            if assume_r == "TRUE":
                total_assume_true += 1
            if assert_r == "TRUE":
                total_assert_true += 1

        correct_samples = [
            sample
            for sample in samples
            if canonical_result(
                (sample.get("assert_verification_result") or {}).get("result")
            )
            == "TRUE"
        ]
        bench_correct = len(correct_samples) > 0
        if bench_correct:
            corr_benchmarks += 1

        best = min(samples, key=sample_total_time)
        best_correct = (
            min(correct_samples, key=sample_total_time) if correct_samples else None
        )
        first_correct = (
            min(correct_samples, key=lambda sample: sample.get("sample_id", 0))
            if correct_samples
            else None
        )

        e2e = sample_total_time(best)
        dr = canonical_result(best.get("result"))
        a_r = canonical_result((best.get("assume_verification_result") or {}).get("result"))
        t_r = canonical_result((best.get("assert_verification_result") or {}).get("result"))

        fastest_correct_e2e = (
            sample_total_time(best_correct) if best_correct is not None else None
        )
        fastest_correct_idx = (
            best_correct.get("sample_id", -1) if best_correct is not None else -1
        )

        first_correct_e2e = (
            sample_total_time(first_correct) if first_correct is not None else None
        )
        first_correct_idx = (
            first_correct.get("sample_id", -1) if first_correct is not None else -1
        )

        is_real_faster_first = (
            bench_correct
            and first_correct_e2e is not None
            and bt > 0
            and first_correct_e2e < bt * tolerance
        )
        is_real_faster_fastest = (
            bench_correct
            and fastest_correct_e2e is not None
            and bt > 0
            and fastest_correct_e2e < bt * tolerance
        )

        is_raw_faster = bt > 0 and e2e < bt * tolerance
        speedup = bt / e2e if e2e > 0 else 0.0

        official_ext: Dict[str, bool] = {}
        for timeout in timeouts:
            official_ext[str(timeout)] = bench_correct and model_solved_at(
                correct_results, fname, timeout
            ) and not baseline_solved_at(baseline_lookup, fname, timeout)

        if br == "TRUE" and not bench_correct:
            category = "regression"
        elif is_raw_faster and not bench_correct:
            category = "faster_but_not_solved"
        elif not bench_correct:
            category = "both_false_or_incomparable"
        elif br != "TRUE" and bench_correct:
            category = "semantic_extension"
        elif bench_correct and is_real_faster_fastest:
            category = "solved_and_faster"
        elif bench_correct and not is_real_faster_fastest:
            sp = bt / (fastest_correct_e2e or bt) if bt > 0 else 1.0
            category = "correct_but_slower" if sp < tolerance else "correct_no_effect"
        else:
            category = "both_false_or_incomparable"

        rows.append(
            {
                "benchmark": fname,
                "baseline_result": br,
                "baseline_time": bt,
                "deepseek_result": dr,
                "deepseek_time": round(e2e, 1),
                "generation_time": round(
                    to_float(best.get("generation_time")) or 0.0, 1
                ),
                "verify_time": round(
                    max(
                        to_float(best.get("assume_verification_time")) or 0.0,
                        to_float(best.get("assert_verification_time")) or 0.0,
                    ),
                    1,
                ),
                "assume_result": a_r,
                "assert_result": t_r,
                "is_correct": bench_correct,
                "is_raw_faster": is_raw_faster,
                "first_correct_idx": first_correct_idx,
                "first_correct_e2e": (
                    round(first_correct_e2e, 1) if first_correct_e2e is not None else None
                ),
                "fastest_correct_idx": fastest_correct_idx,
                "fastest_correct_e2e": (
                    round(fastest_correct_e2e, 1)
                    if fastest_correct_e2e is not None
                    else None
                ),
                "solved_first": is_real_faster_first,
                "solved_fastest": is_real_faster_fastest,
                "official_ext": official_ext,
                "speedup": round(speedup, 3),
                "category": category,
            }
        )

    counts: Dict[str, int] = {}
    official_ext_counts = {str(timeout): 0 for timeout in timeouts}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
        if row["solved_first"]:
            counts["solved_and_faster_first"] = counts.get("solved_and_faster_first", 0) + 1
        if row["solved_fastest"]:
            counts["solved_and_faster_fastest"] = counts.get(
                "solved_and_faster_fastest", 0
            ) + 1
        for timeout in timeouts:
            if row["official_ext"].get(str(timeout)):
                official_ext_counts[str(timeout)] += 1

    real_improvements_first = counts.get("solved_and_faster_first", 0)
    real_improvements_fastest = counts.get("solved_and_faster_fastest", 0)
    raw_e2e_faster = sum(1 for row in rows if row["is_raw_faster"])

    result_hash = hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    return {
        "source": str(results_path),
        "baseline": str(baseline_path),
        "timeouts": timeouts,
        "tolerance": tolerance,
        "result_sha256": result_hash,
        "n_benchmarks": len(rows),
        "total_samples": total_samples,
        "extraction_rate": f"{total_extracted}/{total_samples}",
        "assume_true": f"{total_assume_true}/{total_samples}",
        "assert_true": f"{total_assert_true}/{total_samples}",
        "corr_count": corr_benchmarks,
        "corr_pct": f"{corr_benchmarks}/{len(rows)}",
        "raw_e2e_faster": raw_e2e_faster,
        "real_improvements_first_correct": real_improvements_first,
        "real_improvements_fastest_correct": real_improvements_fastest,
        "official_ext_counts": official_ext_counts,
        "semantic_extension_count": counts.get("semantic_extension", 0),
        "counts": counts,
        "rows": rows,
    }


def print_report(meta: dict, fmt: str = "table") -> None:
    counts = meta["counts"]
    rows = meta["rows"]
    timeouts = meta["timeouts"]

    if fmt == "table":
        print(
            f"{'Benchmark':45s} {'Base':5s} {'BT':>7s} {'DS':5s} {'DST':>7s} "
            f"{'Sp':>6s} {'Cor':4s} {'1st':4s} {'Category'}"
        )
        print("-" * 110)
        for row in rows:
            print(
                f"{row['benchmark']:45s} {row['baseline_result']:5s} {row['baseline_time']:7.0f}s "
                f"{row['deepseek_result']:5s} {row['deepseek_time']:7.0f}s {row['speedup']:5.1f}x "
                f"{'Y' if row['is_correct'] else 'N':>4s} "
                f"{'Y' if row['solved_first'] else 'N':>4s} {row['category']}"
            )

    print("\n=== Summary ===")
    print(f"  #Corr: {meta['corr_count']}/{meta['n_benchmarks']}")
    print(f"  Samples: {meta['total_samples']}")
    print(f"  Extracted: {meta['extraction_rate']}")
    print(f"  assume=TRUE (sample-level): {meta['assume_true']}")
    print(f"  assert=TRUE (sample-level): {meta['assert_true']}")
    print(f"  raw E2E faster (misleading): {meta['raw_e2e_faster']}/{meta['n_benchmarks']}")
    print(
        "  REAL improvements (first-correct E2E): "
        f"{meta['real_improvements_first_correct']}/{meta['n_benchmarks']}"
    )
    print(
        "  REAL improvements (fastest-correct E2E): "
        f"{meta['real_improvements_fastest_correct']}/{meta['n_benchmarks']}"
    )
    print()
    for timeout in timeouts:
        label = f"{int(timeout)}s" if int(timeout) == timeout else f"{timeout:g}s"
        print(
            f"  Official #Ext@{label} (print_results.py semantics): "
            f"{meta['official_ext_counts'][str(timeout)]}"
        )
    print(f"  semantic_extension (audited, not #Ext@T): {meta['semantic_extension_count']}")
    print()
    print(f"  solved_and_faster:         {counts.get('solved_and_faster', 0)}")
    print(f"  solved_and_faster_first:   {counts.get('solved_and_faster_first', 0)}")
    print(f"  solved_and_faster_fastest: {counts.get('solved_and_faster_fastest', 0)}")
    print(f"  semantic_extension:        {counts.get('semantic_extension', 0)}")
    print(f"  faster_but_not_solved:     {counts.get('faster_but_not_solved', 0)}  ← NOT improvements")
    print(f"  correct_but_slower:        {counts.get('correct_but_slower', 0)}")
    print(f"  correct_no_effect:         {counts.get('correct_no_effect', 0)}")
    print(f"  regression:                {counts.get('regression', 0)}")
    print(f"  both_false_or_incomparable: {counts.get('both_false_or_incomparable', 0)}")

    if fmt == "csv":
        ext_cols = ",".join(f"official_ext_{int(t)}s" for t in timeouts)
        header = (
            "benchmark,baseline_result,baseline_time,deepseek_result,deepseek_time,"
            "assume_result,assert_result,is_correct,is_raw_faster,solved_first,"
            f"speedup,category,{ext_cols}"
        )
        print(header)
        for row in rows:
            ext_vals = ",".join(
                str(int(row["official_ext"].get(str(timeout), False)))
                for timeout in timeouts
            )
            print(
                f"{row['benchmark']},{row['baseline_result']},{row['baseline_time']:.1f},"
                f"{row['deepseek_result']},{row['deepseek_time']:.1f},"
                f"{row['assume_result']},{row['assert_result']},{row['is_correct']},"
                f"{row['is_raw_faster']},{row['solved_first']},{row['speedup']:.3f},"
                f"{row['category']},{ext_vals}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Quokka benchmark results (aligned with print_results.py)"
    )
    parser.add_argument("results", help="Path to result JSON")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINES["uautomizer"],
        help="Path to baseline timing JSON",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.95,
        help="Speedup tolerance factor (default: 0.95 = 5%% faster)",
    )
    parser.add_argument(
        "--timeouts",
        type=float,
        nargs="+",
        default=[30.0, 500.0],
        help="Timeouts for official #Ext@T (default: 30 500)",
    )
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table")
    args = parser.parse_args()

    meta = analyze(
        Path(args.results).resolve(),
        args.baseline.resolve(),
        args.tolerance,
        sorted(args.timeouts),
    )

    if args.format == "json":
        print(json.dumps(meta, indent=2, default=str))
    else:
        print_report(meta, args.format)


if __name__ == "__main__":
    main()
