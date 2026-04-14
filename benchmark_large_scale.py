#!/usr/bin/env python3
"""
ChainMind Large-Scale Merkle Tree Benchmark
============================================
Extends Table 2 in the NBC'26 paper with 50,000 and 100,000 batch sizes.

Usage:
    conda activate chainmind
    python benchmark_large_scale.py

Output: prints results in both human-readable and LaTeX table row format.
"""

import hashlib
import time
import os
import math
import statistics
from typing import List, Tuple

# ---------------------------------------------------------------------------
# 1. Keccak-256 helper (same as Solidity's keccak256)
# ---------------------------------------------------------------------------
try:
    from Crypto.Hash import keccak  # pycryptodome
    def keccak256(data: bytes) -> bytes:
        k = keccak.new(digest_bits=256)
        k.update(data)
        return k.digest()
except ImportError:
    # fallback: use pysha3 or web3
    try:
        from web3 import Web3
        def keccak256(data: bytes) -> bytes:
            return Web3.keccak(data)
    except ImportError:
        import sha3  # pysha3
        def keccak256(data: bytes) -> bytes:
            k = sha3.keccak_256()
            k.update(data)
            return k.digest()


# ---------------------------------------------------------------------------
# 2. Generate synthetic decision leaf hashes
# ---------------------------------------------------------------------------
def generate_leaves(n: int) -> List[bytes]:
    """
    Simulate n agent decisions.
    Each decision -> SHA-256(input) || SHA-256(output) || SHA-256(model_meta)
    -> keccak256(abi.encodePacked(...)) = leaf hash (32 bytes)
    """
    leaves = []
    for i in range(n):
        # Simulate three SHA-256 hashes per decision
        h_input  = hashlib.sha256(f"prompt_{i}_{os.urandom(8).hex()}".encode()).digest()
        h_output = hashlib.sha256(f"response_{i}_{os.urandom(8).hex()}".encode()).digest()
        h_model  = hashlib.sha256(f"model_qwen2.5-7b_v1_{i}".encode()).digest()
        # Combine into leaf via keccak256(abi.encodePacked(h_input, h_output, h_model))
        leaf = keccak256(h_input + h_output + h_model)
        leaves.append(leaf)
    return leaves


# ---------------------------------------------------------------------------
# 3. Build Merkle tree (sorted-pair, matches Solidity contract)
# ---------------------------------------------------------------------------
def build_merkle_tree(leaves: List[bytes]) -> Tuple[bytes, List[List[bytes]]]:
    """
    Build a Merkle tree with sorted sibling pairs (matching ChainMind contract).
    Returns: (root, all_levels) where all_levels[0] = leaves.
    """
    if not leaves:
        raise ValueError("Empty leaf list")

    current_level = list(leaves)
    all_levels = [current_level]

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                left, right = current_level[i], current_level[i + 1]
            else:
                # Odd number of nodes: duplicate last
                left, right = current_level[i], current_level[i]
            # Sort siblings before hashing (same as contract)
            if left <= right:
                parent = keccak256(left + right)
            else:
                parent = keccak256(right + left)
            next_level.append(parent)
        current_level = next_level
        all_levels.append(current_level)

    return current_level[0], all_levels


# ---------------------------------------------------------------------------
# 4. Generate Merkle proof for a given leaf index
# ---------------------------------------------------------------------------
def get_merkle_proof(all_levels: List[List[bytes]], index: int) -> List[bytes]:
    """Get the Merkle proof (sibling hashes) for leaf at `index`."""
    proof = []
    idx = index
    for level in all_levels[:-1]:  # skip root level
        if idx % 2 == 0:
            sibling_idx = idx + 1
        else:
            sibling_idx = idx - 1
        if sibling_idx < len(level):
            proof.append(level[sibling_idx])
        else:
            proof.append(level[idx])  # duplicate (odd count)
        idx = idx // 2
    return proof


# ---------------------------------------------------------------------------
# 5. Verify a Merkle proof (mirrors on-chain verifyDecision logic)
# ---------------------------------------------------------------------------
def verify_merkle_proof(leaf: bytes, proof: List[bytes], index: int, root: bytes) -> bool:
    """Verify that `leaf` is included in the tree with the given `root`."""
    computed = leaf
    idx = index
    for sibling in proof:
        if idx % 2 == 0:
            if computed <= sibling:
                computed = keccak256(computed + sibling)
            else:
                computed = keccak256(sibling + computed)
        else:
            if sibling <= computed:
                computed = keccak256(sibling + computed)
            else:
                computed = keccak256(computed + sibling)
        idx = idx // 2
    return computed == root


# ---------------------------------------------------------------------------
# 6. Benchmark runner
# ---------------------------------------------------------------------------
def run_benchmark(batch_size: int, num_runs: int = 5) -> dict:
    """
    Run the full benchmark for a given batch size.
    Returns dict with median build_ms, verify_us, depth, proof_bytes.
    """
    build_times = []
    verify_times = []

    for run in range(num_runs):
        # Generate leaves
        leaves = generate_leaves(batch_size)

        # Benchmark: build Merkle tree
        t0 = time.perf_counter()
        root, all_levels = build_merkle_tree(leaves)
        t1 = time.perf_counter()
        build_ms = (t1 - t0) * 1000
        build_times.append(build_ms)

        # Benchmark: verify a random leaf (pick middle leaf for consistency)
        test_index = batch_size // 2
        proof = get_merkle_proof(all_levels, test_index)

        t2 = time.perf_counter()
        result = verify_merkle_proof(leaves[test_index], proof, test_index, root)
        t3 = time.perf_counter()
        verify_us = (t3 - t2) * 1_000_000
        verify_times.append(verify_us)

        assert result, f"Verification failed for batch_size={batch_size}, run={run}"

    depth = math.ceil(math.log2(batch_size))
    proof_bytes = depth * 32

    return {
        "batch_size": batch_size,
        "build_ms": round(statistics.median(build_times), 1),
        "verify_us": round(statistics.median(verify_times)),
        "depth": depth,
        "proof_bytes": proof_bytes,
        "build_times_all": [round(t, 1) for t in build_times],
        "verify_times_all": [round(t) for t in verify_times],
    }


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------
def main():
    # All batch sizes: original Table 2 + new 50K, 100K
    batch_sizes = [10, 50, 100, 500, 1_000, 5_000, 10_000, 50_000, 100_000]
    num_runs = 5

    print("=" * 72)
    print("ChainMind Large-Scale Merkle Tree Benchmark")
    print(f"Runs per batch size: {num_runs} (reporting median)")
    print("=" * 72)

    results = []
    for bs in batch_sizes:
        print(f"\n>>> Running batch_size = {bs:>7,d} ...", end=" ", flush=True)
        r = run_benchmark(bs, num_runs)
        results.append(r)
        print(f"Done. Build={r['build_ms']:.1f} ms, Verify={r['verify_us']} μs")

    # ── Pretty-print results table ──
    print("\n" + "=" * 72)
    print(f"{'Batch Size':>12} {'Build (ms)':>12} {'Verify (μs)':>12} {'Depth':>6} {'Proof (B)':>10}")
    print("-" * 72)
    for r in results:
        print(f"{r['batch_size']:>12,d} {r['build_ms']:>12.1f} {r['verify_us']:>12d} {r['depth']:>6d} {r['proof_bytes']:>10d}")
    print("=" * 72)

    # ── LaTeX rows (copy-paste into Table 2) ──
    print("\n📋 LaTeX rows for Table 2 (copy-paste into your .tex file):")
    print("-" * 72)
    for r in results:
        # Format build_ms: use comma for thousands
        if r['build_ms'] >= 1000:
            build_str = f"{r['build_ms']:,.0f}"
        else:
            build_str = f"{r['build_ms']:.1f}" if r['build_ms'] < 100 else f"{r['build_ms']:.0f}"
        print(f"{r['batch_size']:,d} & {build_str} & {r['verify_us']} & {r['depth']} & {r['proof_bytes']} \\\\")
    print("-" * 72)

    # ── Proof size efficiency rows (for Table 4) ──
    print("\n📋 New rows for Table 4 (Proof Size Efficiency):")
    print("-" * 72)
    for r in results:
        if r['batch_size'] in [50_000, 100_000]:
            full_replay = r['batch_size'] * 96  # 3 * 32 bytes per decision
            reduction = full_replay / r['proof_bytes']
            if full_replay >= 1_000_000:
                replay_str = f"{full_replay / 1_000_000:.1f} MB"
            else:
                replay_str = f"{full_replay / 1_000:.0f} KB"
            print(f"{r['batch_size']:,d} & {r['proof_bytes']} B & {replay_str} & {reduction:,.0f}$\\times$ \\\\")
    print("-" * 72)

    # ── Raw data for reproducibility ──
    print("\n📊 Raw data (all 5 runs):")
    for r in results:
        if r['batch_size'] in [50_000, 100_000]:
            print(f"\n  Batch {r['batch_size']:,d}:")
            print(f"    Build (ms): {r['build_times_all']}")
            print(f"    Verify (μs): {r['verify_times_all']}")


if __name__ == "__main__":
    main()
