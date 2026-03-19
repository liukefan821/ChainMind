"""
pipeline.py — End-to-end ChainMind pipeline.

1. Generate LLM agent decisions (via Ollama or mock)
2. Build Merkle tree from decision hashes
3. Deploy / interact with smart contract on Sepolia
4. Submit Merkle root on-chain
5. Verify individual decisions with Merkle proofs

Author: Kefan Liu
Project: ChainMind — NBC'26
"""

import json
import time
import argparse
from pathlib import Path

from merkle_tree import MerkleTree, DecisionRecord, benchmark_tree
from agent_simulator import generate_decisions, save_decisions


def run_pipeline(num_decisions: int = 10, use_ollama: bool = True,
                 output_dir: str = "data"):
    """Run the complete ChainMind pipeline."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ============ Step 1: Generate agent decisions ============
    print("\n" + "=" * 60)
    print("STEP 1: Generating LLM agent decisions")
    print("=" * 60)

    records = generate_decisions(num_decisions, use_ollama=use_ollama)
    save_decisions(records, str(out / "decisions.json"))

    # ============ Step 2: Build Merkle tree ============
    print("\n" + "=" * 60)
    print("STEP 2: Building Merkle tree")
    print("=" * 60)

    leaves = [r.leaf_hash for r in records]
    tree = MerkleTree(leaves)

    stats = tree.get_stats()
    print(f"  Leaves:     {stats['num_leaves']}")
    print(f"  Tree depth: {stats['depth']}")
    print(f"  Root:       {stats['root_hex']}")
    print(f"  Proof size: {stats['proof_bytes_per_leaf']} bytes/leaf")

    # ============ Step 3: Generate proofs for all leaves ============
    print("\n" + "=" * 60)
    print("STEP 3: Generating Merkle proofs")
    print("=" * 60)

    proofs_data = []
    for i, record in enumerate(records):
        proof, directions = tree.get_proof(i)
        # Local verification
        is_valid = tree.verify_proof(record.leaf_hash, proof, i)

        proof_entry = {
            "index": i,
            "leaf_hash": "0x" + record.leaf_hash.hex(),
            "proof": ["0x" + p.hex() for p in proof],
            "directions": directions,
            "verified_locally": is_valid,
        }
        proofs_data.append(proof_entry)

        status = "VALID" if is_valid else "INVALID"
        print(f"  Decision {i:>3}: {status} "
              f"(proof: {len(proof)} hashes, {len(proof)*32}B)")

    # Save proofs
    proof_file = out / "merkle_proofs.json"
    proof_output = {
        "merkle_root": tree.root_hex,
        "num_leaves": len(records),
        "tree_depth": tree.depth,
        "proofs": proofs_data,
    }
    with open(proof_file, 'w') as f:
        json.dump(proof_output, f, indent=2)
    print(f"\n  Proofs saved to {proof_file}")

    # ============ Step 4: Tamper detection demo ============
    print("\n" + "=" * 60)
    print("STEP 4: Tamper detection demonstration")
    print("=" * 60)

    # Tamper with one decision and show detection
    if len(records) > 0:
        original_leaf = records[0].leaf_hash
        proof, _ = tree.get_proof(0)

        # Create a tampered record
        tampered = DecisionRecord(
            input_prompt=records[0].input_prompt,
            output_response=records[0].output_response + " [TAMPERED]",
            model_id=records[0].model_id,
            model_version=records[0].model_version,
        )

        tampered_valid = tree.verify_proof(tampered.leaf_hash, proof, 0)
        original_valid = tree.verify_proof(original_leaf, proof, 0)

        print(f"  Original decision: {'VALID' if original_valid else 'INVALID'}")
        print(f"  Tampered decision: {'VALID' if tampered_valid else 'INVALID'}")
        print(f"  Tamper detected:   {not tampered_valid}")
        print(f"  Original leaf:  {('0x' + original_leaf.hex())[:42]}...")
        print(f"  Tampered leaf:  {('0x' + tampered.leaf_hash.hex())[:42]}...")

    # ============ Step 5: Performance benchmarks ============
    print("\n" + "=" * 60)
    print("STEP 5: Performance benchmarks (for paper Table 1)")
    print("=" * 60)

    sizes = [10, 50, 100, 500, 1000, 5000, 10000]
    bench_results = []

    print(f"\n{'Leaves':>8} | {'Build(ms)':>10} | {'Proof(μs)':>10} | "
          f"{'Verify(μs)':>10} | {'Depth':>5}")
    print("-" * 60)

    for n in sizes:
        result = benchmark_tree(n)
        bench_results.append(result)
        print(f"{result['num_leaves']:>8} | "
              f"{result['build_time_ms']:>10.2f} | "
              f"{result['proof_gen_time_us']:>10.2f} | "
              f"{result['verify_time_us']:>10.2f} | "
              f"{result['tree_depth']:>5}")

    # Save benchmarks
    bench_file = out / "benchmarks.json"
    with open(bench_file, 'w') as f:
        json.dump(bench_results, f, indent=2)
    print(f"\n  Benchmarks saved to {bench_file}")

    # ============ Step 6: Generate blockchain submission data ============
    print("\n" + "=" * 60)
    print("STEP 6: Blockchain submission data (for Remix IDE)")
    print("=" * 60)

    print(f"\n  Copy these values to Remix IDE to call submitBatch():")
    print(f"  _merkleRoot: {tree.root_hex}")
    print(f"  _batchSize:  {len(records)}")
    print(f'  _modelId:    "qwen2.5:7b"')

    # Verification data for verifyDecision()
    if proofs_data:
        p = proofs_data[0]
        print(f"\n  To verify decision 0, call verifyDecision() with:")
        print(f"  _batchId:  0  (or your batch number)")
        print(f"  _leafHash: {p['leaf_hash']}")
        print(f"  _proof:    {json.dumps(p['proof'])}")
        print(f"  _index:    0")

    # Save Remix-ready data
    remix_file = out / "remix_submission.json"
    remix_data = {
        "submitBatch": {
            "_merkleRoot": tree.root_hex,
            "_batchSize": len(records),
            "_modelId": "qwen2.5:7b",
        },
        "verifyDecision_example": {
            "_batchId": 0,
            "_leafHash": proofs_data[0]["leaf_hash"] if proofs_data else "",
            "_proof": proofs_data[0]["proof"] if proofs_data else [],
            "_index": 0,
        },
        "individual_decisions": [
            {
                "commitDecision": {
                    "_inputHash": "0x" + r.input_hash.hex(),
                    "_outputHash": "0x" + r.output_hash.hex(),
                    "_modelHash": "0x" + r.model_hash.hex(),
                }
            }
            for r in records[:3]  # First 3 for individual commit demo
        ]
    }
    with open(remix_file, 'w') as f:
        json.dump(remix_data, f, indent=2)
    print(f"\n  Remix submission data saved to {remix_file}")

    # ============ Summary ============
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Decisions generated: {len(records)}")
    print(f"  Merkle root:        {tree.root_hex}")
    print(f"  Tree depth:         {tree.depth}")
    print(f"  All proofs valid:   {all(p['verified_locally'] for p in proofs_data)}")
    print(f"\n  Output files:")
    print(f"    {out / 'decisions.json'}")
    print(f"    {out / 'merkle_proofs.json'}")
    print(f"    {out / 'benchmarks.json'}")
    print(f"    {out / 'remix_submission.json'}")
    print(f"\n  Next step: Deploy contract on Remix IDE → Submit batch on-chain")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChainMind Full Pipeline")
    parser.add_argument("-n", "--num", type=int, default=10,
                        help="Number of decisions to generate")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock LLM responses")
    parser.add_argument("-o", "--output", type=str, default="data",
                        help="Output directory")
    args = parser.parse_args()

    run_pipeline(
        num_decisions=args.num,
        use_ollama=not args.mock,
        output_dir=args.output,
    )
