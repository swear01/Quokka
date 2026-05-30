#!/usr/bin/env python3
"""Analyze DeepSeek Quokka benchmark results with proper classification.

Categories:
  solved_and_faster       invariant correct (assert=TRUE) AND end-to-end faster
  extension               baseline NOT solved but DeepSeek assert=TRUE (new solve)
  correct_but_slower      invariant correct but end-to-end same or slower
  correct_no_effect       invariant correct, baseline time ≈ DeepSeek time
  faster_but_not_solved   raw end-to-end faster but invariant rejected (NOT an improvement)
  regression              baseline solved, DeepSeek invariant rejected (assert≠TRUE)
  both_false_or_incomparable  both baseline and DeepSeek unsolved, or unclassifiable

Only solved_and_faster + extension count as real verification improvements.
raw_e2e_faster must never be called "improvement".
"""
import json, hashlib, sys, argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

def canonical_result(result: Any) -> str:
    if result is None:
        return "UNKNOWN"
    r = str(result).strip().upper()
    if r in ("TRUE", "FALSE", "TIMEOUT", "UNKNOWN"):
        return r
    return "UNKNOWN"

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def analyze(results_path: str, baseline_path: str, tolerance: float = 0.95) -> dict:
    results = load_json(results_path)
    baseline = load_json(baseline_path)
    baseline_lookup = {}
    for entry in baseline:
        if isinstance(entry, dict) and "filename" in entry:
            baseline_lookup[entry["filename"]] = entry

    rows: List[dict] = []
    total_extracted = 0
    total_assume_true = 0
    total_assert_true = 0
    total_samples = 0
    corr_benchmarks = 0  # benchmarks with ≥1 assert=TRUE sample

    for fname in sorted(results.keys()):
        base = baseline_lookup.get(fname, {})
        bt = base.get("time_taken", 0.0)
        br = canonical_result(base.get("result"))

        samples = results[fname]
        if not samples:
            continue

        def sample_e2e(s):
            gen = s.get("generation_time", 0) or 0
            avt = s.get("assume_verification_time", 0) or 0
            ast = s.get("assert_verification_time", 0) or 0
            return gen + max(avt, ast)

        # #Corr: at least one sample has assert=TRUE
        correct_samples = [
            s for s in samples
            if canonical_result((s.get("assert_verification_result") or {}).get("result")) == "TRUE"
        ]
        bench_correct = len(correct_samples) > 0
        if bench_correct:
            corr_benchmarks += 1

        # Best overall sample (for reporting)
        best = min(samples, key=sample_e2e)

        # Best CORRECT sample (for real improvement metrics)
        best_correct = min(correct_samples, key=sample_e2e) if correct_samples else None

        # FIRST correct sample (smallest sample_id with assert=TRUE) — conservative metric
        first_correct = min(correct_samples, key=lambda s: s.get("sample_id", 0)) if correct_samples else None

        gen = best.get("generation_time", 0) or 0
        avt = best.get("assume_verification_time", 0) or 0
        ast = best.get("assert_verification_time", 0) or 0
        verify_time = max(avt, ast)
        e2e = gen + verify_time
        dr = canonical_result(best.get("result"))
        a_r = canonical_result((best.get("assume_verification_result") or {}).get("result"))
        t_r = canonical_result((best.get("assert_verification_result") or {}).get("result"))

        # E2E for real improvement
        if best_correct:
            cgen = best_correct.get("generation_time", 0) or 0
            cavt = best_correct.get("assume_verification_time", 0) or 0
            cast = best_correct.get("assert_verification_time", 0) or 0
            fastest_correct_e2e = cgen + max(cavt, cast)
            fastest_correct_idx = best_correct.get("sample_id", -1)
        else:
            fastest_correct_e2e = None
            fastest_correct_idx = -1

        if first_correct:
            fgen = first_correct.get("generation_time", 0) or 0
            favt = first_correct.get("assume_verification_time", 0) or 0
            fast = first_correct.get("assert_verification_time", 0) or 0
            first_correct_e2e = fgen + max(favt, fast)
            first_correct_idx = first_correct.get("sample_id", -1)
        else:
            first_correct_e2e = None
            first_correct_idx = -1

        is_real_faster_first = bench_correct and first_correct_e2e is not None and first_correct_e2e < bt * tolerance
        is_real_faster_fastest = bench_correct and fastest_correct_e2e is not None and fastest_correct_e2e < bt * tolerance

        is_raw_faster = e2e < bt * tolerance
        base_solved = br == "TRUE"
        speedup = bt / e2e if e2e > 0 else 0

        # Classification (use fastest-correct for category)
        if bench_correct and is_real_faster_fastest:
            category = "solved_and_faster"
        elif not base_solved and bench_correct:
            category = "extension"
        elif is_raw_faster and not bench_correct:
            category = "faster_but_not_solved"
        elif bench_correct and not is_real_faster_fastest:
            sp = bt / (fastest_correct_e2e or bt)
            if sp < tolerance:
                category = "correct_but_slower"
            else:
                category = "correct_no_effect"
        elif base_solved and not bench_correct:
            category = "regression"
        else:
            category = "both_false_or_incomparable"

        rows.append({
            "benchmark": fname,
            "baseline_result": br,
            "baseline_time": bt,
            "deepseek_result": dr,
            "deepseek_time": e2e,
            "generation_time": gen,
            "verify_time": verify_time,
            "assume_result": a_r,
            "assert_result": t_r,
            "is_correct": bench_correct,
            "is_raw_faster": is_raw_faster,
            "first_correct_idx": first_correct_idx,
            "first_correct_e2e": round(first_correct_e2e, 1) if first_correct_e2e else None,
            "fastest_correct_idx": fastest_correct_idx,
            "fastest_correct_e2e": round(fastest_correct_e2e, 1) if fastest_correct_e2e else None,
            "solved_first": is_real_faster_first,
            "solved_fastest": is_real_faster_fastest,
            "speedup": speedup,
            "category": category,
        })

    # Compute counts from rows (single source of truth)
    counts = {}
    for r in rows:
        cat = r["category"]
        counts[cat] = counts.get(cat, 0) + 1
        if r["solved_fastest"]:
            counts["solved_and_faster_fastest"] = counts.get("solved_and_faster_fastest", 0) + 1
        if r["solved_first"]:
            counts["solved_and_faster_first"] = counts.get("solved_and_faster_first", 0) + 1

    real_improvements_first = counts.get("solved_and_faster_first", 0) + counts.get("extension", 0)
    real_improvements_fastest = counts.get("solved_and_faster_fastest", 0) + counts.get("extension", 0)
    raw_e2e_faster = real_improvements_fastest + counts.get("faster_but_not_solved", 0)

    result_hash = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()[:16]

    real_improvements_first = counts.get("solved_and_faster_first", 0) + counts.get("extension", 0)
    real_improvements_fastest = counts.get("solved_and_faster_fastest", 0) + counts.get("extension", 0)
    raw_e2e_faster = real_improvements_fastest + counts.get("faster_but_not_solved", 0)

    result_hash = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()[:16]

    return {
        "source": results_path,
        "baseline": baseline_path,
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
        "counts": counts,
        "rows": rows,
    }


def print_report(meta: dict, fmt: str = "table"):
    counts = meta["counts"]
    rows = meta["rows"]

    if fmt == "table":
        print(f"{'Benchmark':45s} {'Base':5s} {'BT':>7s} {'DS':5s} {'DST':>7s} {'Sp':>6s} {'Cor':4s} {'Fst':4s} {'Category'}")
        print("-" * 110)
        for r in rows:
            print(f"{r['benchmark']:45s} {r['baseline_result']:5s} {r['baseline_time']:7.0f}s {r['deepseek_result']:5s} {r['deepseek_time']:7.0f}s {r['speedup']:5.1f}x {'Y' if r['is_correct'] else 'N':>4s} {'Y' if r['is_raw_faster'] else 'N':>4s} {r['category']}")

    print(f"\n=== Summary ===")
    print(f"  #Corr: {meta['corr_count']}/{meta['n_benchmarks']}")
    print(f"  raw E2E faster (misleading): {meta['raw_e2e_faster']}/{meta['n_benchmarks']}")
    print(f"  REAL improvements (first-correct):  {meta['real_improvements_first_correct']}/{meta['n_benchmarks']}")
    print(f"  REAL improvements (fastest-correct): {meta['real_improvements_fastest_correct']}/{meta['n_benchmarks']}")
    print()
    print(f"  solved_and_faster_first:   {counts.get('solved_and_faster_first', 0)}")
    print(f"  solved_and_faster_fastest: {counts.get('solved_and_faster_fastest', 0)}")
    print(f"  extension:                 {counts.get('extension', 0)}")
    print(f"  faster_but_not_solved:     {counts.get('faster_but_not_solved', 0)}  ← NOT improvements")
    print(f"  correct_but_slower:        {counts.get('correct_but_slower', 0)}")
    print(f"  correct_no_effect:         {counts.get('correct_no_effect', 0)}")
    print(f"  regression:                {counts.get('regression', 0)}")
    print(f"  both_false_or_incomparable: {counts.get('both_false_or_incomparable', 0)}")

    if fmt == "csv":
        header = "benchmark,baseline_result,baseline_time,deepseek_result,deepseek_time,generation_time,verify_time,assume_result,assert_result,is_correct,is_raw_faster,speedup,category"
        print(header)
        for r in rows:
            print(f"{r['benchmark']},{r['baseline_result']},{r['baseline_time']:.1f},{r['deepseek_result']},{r['deepseek_time']:.1f},{r['generation_time']:.1f},{r['verify_time']:.1f},{r['assume_result']},{r['assert_result']},{r['is_correct']},{r['is_raw_faster']},{r['speedup']:.3f},{r['category']}")


def main():
    parser = argparse.ArgumentParser(description="Analyze DeepSeek Quokka benchmark results")
    parser.add_argument("results", help="Path to result JSON")
    parser.add_argument("--baseline", default="/home/swear01/Quokka/Dataset/timing_uautomizer.json",
                        help="Path to baseline timing JSON")
    parser.add_argument("--tolerance", type=float, default=0.95,
                        help="Speedup tolerance factor (default: 0.95 = 5% faster)")
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table")
    args = parser.parse_args()

    meta = analyze(args.results, args.baseline, args.tolerance)

    if args.format == "json":
        out = {k: v for k, v in meta.items() if k != "rows"}
        out["rows"] = meta["rows"]
        print(json.dumps(out, indent=2, default=str))
    else:
        print_report(meta, args.format)


if __name__ == "__main__":
    main()
