#!/usr/bin/env python3
"""
benchmark_extended.py — Extended benchmark for ChainMind NBC'26 paper.

Adds 50,000 and 100,000 batch sizes to Table 2.
Uses the ORIGINAL merkle_tree.py (Web3.solidity_keccak) to ensure
data consistency with existing results.

Usage:
    cd ~/Projects/ChainMind/scripts
    conda activate chainmind
    python benchmark_extended.py

Author: Kefan Liu
"""

import statistics
from merkle_tree import benchmark_tree

NUM_RUNS = 5  # Paper says "median of 5 runs"

# All batch sizes: original Table 2 + new 50K, 100K
BATCH_SIZES = [10, 50, 100, 500, 1_000, 5_000, 10_000, 50_000, 100_000]


def run_all():
    print("=" * 75)
    print("ChainMind Extended Benchmark (using original merkle_tree.py)")
    print(f"Runs per batch size: {NUM_RUNS} (reporting median)")
    print("=" * 75)

    all_results = []

    for bs in BATCH_SIZES:
        print(f"\n>>> Batch size = {bs:>7,d}")
        build_times = []
        verify_times = []

        for run in range(NUM_RUNS):
            r = benchmark_tree(bs, num_verify=100)
            build_times.append(r["build_time_ms"])
            verify_times.append(r["verify_time_us"])
            print(f"    Run {run+1}/{NUM_RUNS}: "
                  f"Build={r['build_time_ms']:.2f} ms, "
                  f"Verify={r['verify_time_us']:.1f} μs")

        median_build = statistics.median(build_times)
        median_verify = statistics.median(verify_times)
        depth = r["tree_depth"]
        proof_bytes = r["proof_size_bytes"]

        all_results.append({
            "batch_size": bs,
            "build_ms": median_build,
            "verify_us": median_verify,
            "depth": depth,
            "proof_bytes": proof_bytes,
            "build_all": build_times,
            "verify_all": verify_times,
        })

        print(f"    → Median: Build={median_build:.2f} ms, "
              f"Verify={median_verify:.1f} μs")

    # ── Summary table ──
    print("\n" + "=" * 75)
    print(f"{'Batch Size':>12} {'Build (ms)':>12} {'Verify (μs)':>12} "
          f"{'Depth':>6} {'Proof (B)':>10}")
    print("-" * 75)
    for r in all_results:
        print(f"{r['batch_size']:>12,d} {r['build_ms']:>12.2f} "
              f"{r['verify_us']:>12.1f} {r['depth']:>6d} "
              f"{r['proof_bytes']:>10d}")
    print("=" * 75)

    # ── LaTeX rows ──
    print("\n📋 LaTeX rows for Table 2:")
    print("-" * 75)
    for r in all_results:
        # Format build: match paper style
        bms = r["build_ms"]
        if bms >= 1000:
            b_str = f"{bms:,.0f}"
        elif bms >= 100:
            b_str = f"{bms:.0f}"
        elif bms >= 10:
            b_str = f"{bms:.1f}"
        else:
            b_str = f"{bms:.2f}"

        # Format verify: integer
        v_str = f"{r['verify_us']:.0f}"

        print(f"{r['batch_size']:,d} & {b_str} & {v_str} "
              f"& {r['depth']} & {r['proof_bytes']} \\\\")
    print("-" * 75)

    # ── Table 4 new rows ──
    print("\n📋 New rows for Table 4 (Proof Size Efficiency):")
    print("-" * 75)
    for r in all_results:
        if r["batch_size"] in [50_000, 100_000]:
            full = r["batch_size"] * 96
            reduction = full / r["proof_bytes"]
            if full >= 1_000_000:
                f_str = f"{full / 1_000_000:.1f} MB"
            else:
                f_str = f"{full / 1_000:.0f} KB"
            print(f"{r['batch_size']:,d} & {r['proof_bytes']} B "
                  f"& {f_str} & {reduction:,.0f}$\\times$ \\\\")
    print("-" * 75)

    # ── Raw data for 50K/100K ──
    print("\n📊 Raw data (all 5 runs) for new batch sizes:")
    for r in all_results:
        if r["batch_size"] in [50_000, 100_000]:
            print(f"\n  Batch {r['batch_size']:,d}:")
            print(f"    Build (ms):  {[round(x, 2) for x in r['build_all']]}")
            print(f"    Verify (μs): {[round(x, 1) for x in r['verify_all']]}")

    print("\n✅ Done! Copy the 50,000 and 100,000 rows into your .tex file.")


if __name__ == "__main__":
    run_all()
