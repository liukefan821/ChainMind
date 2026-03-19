"""
merkle_tree.py — Merkle tree construction and proof generation for ChainMind.

Uses SHA-256 for leaf hashing and keccak256 for internal nodes
(matching Solidity's keccak256(abi.encodePacked(...))).

Author: Kefan Liu
Project: ChainMind — NBC'26
"""

import hashlib
import json
import time
from typing import List, Tuple, Optional
from eth_abi import encode as abi_encode
from web3 import Web3


def sha256_hash(data: str) -> bytes:
    """Compute SHA-256 hash of a string, return 32 bytes."""
    return hashlib.sha256(data.encode('utf-8')).digest()


def keccak256_pair(left: bytes, right: bytes) -> bytes:
    """
    Compute keccak256(abi.encodePacked(left, right)).
    Matches Solidity's keccak256(abi.encodePacked(a, b)).
    """
    return Web3.solidity_keccak(['bytes32', 'bytes32'], [left, right])


class DecisionRecord:
    """Represents a single LLM agent decision."""

    def __init__(self, input_prompt: str, output_response: str,
                 model_id: str, model_version: str, timestamp: float = None):
        self.input_prompt = input_prompt
        self.output_response = output_response
        self.model_id = model_id
        self.model_version = model_version
        self.timestamp = timestamp or time.time()

        # Compute individual hashes
        self.input_hash = sha256_hash(input_prompt)
        self.output_hash = sha256_hash(output_response)

        model_metadata = json.dumps({
            "model_id": model_id,
            "model_version": model_version,
        }, sort_keys=True)
        self.model_hash = sha256_hash(model_metadata)

    @property
    def leaf_hash(self) -> bytes:
        """
        Compute the leaf hash for Merkle tree inclusion.
        leaf = keccak256(abi.encodePacked(inputHash, outputHash, modelHash))
        """
        return Web3.solidity_keccak(
            ['bytes32', 'bytes32', 'bytes32'],
            [self.input_hash, self.output_hash, self.model_hash]
        )

    def to_dict(self) -> dict:
        return {
            "input_prompt": self.input_prompt,
            "output_response": self.output_response,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "timestamp": self.timestamp,
            "input_hash": "0x" + self.input_hash.hex(),
            "output_hash": "0x" + self.output_hash.hex(),
            "model_hash": "0x" + self.model_hash.hex(),
            "leaf_hash": "0x" + self.leaf_hash.hex(),
        }


class MerkleTree:
    """
    Merkle tree for batch commitment of agent decisions.

    - Leaves are keccak256(inputHash || outputHash || modelHash)
    - Internal nodes are keccak256(left || right)
    - If odd number of leaves, the last leaf is duplicated
    """

    def __init__(self, leaves: List[bytes]):
        if not leaves:
            raise ValueError("Cannot create Merkle tree with empty leaves")

        self.original_leaves = leaves[:]
        self.leaves = leaves[:]
        self.layers: List[List[bytes]] = []
        self._build_tree()

    def _build_tree(self):
        """Build the Merkle tree bottom-up."""
        current_layer = self.leaves[:]

        # Pad to even number
        if len(current_layer) % 2 == 1:
            current_layer.append(current_layer[-1])

        self.layers = [current_layer]

        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1]
                parent = keccak256_pair(left, right)
                next_layer.append(parent)

            # Pad next layer if needed (except root)
            if len(next_layer) > 1 and len(next_layer) % 2 == 1:
                next_layer.append(next_layer[-1])

            self.layers.append(next_layer)
            current_layer = next_layer

    @property
    def root(self) -> bytes:
        """Return the Merkle root."""
        return self.layers[-1][0]

    @property
    def root_hex(self) -> str:
        """Return the Merkle root as hex string."""
        return "0x" + self.root.hex()

    @property
    def depth(self) -> int:
        """Return the depth of the tree."""
        return len(self.layers) - 1

    def get_proof(self, index: int) -> Tuple[List[bytes], List[int]]:
        """
        Generate a Merkle proof for the leaf at the given index.

        Returns:
            proof: list of sibling hashes
            directions: list of 0 (left) or 1 (right) indicating
                        which side the sibling is on
        """
        if index >= len(self.original_leaves):
            raise IndexError(f"Leaf index {index} out of range "
                             f"(tree has {len(self.original_leaves)} leaves)")

        proof = []
        directions = []
        current_index = index

        for layer in self.layers[:-1]:  # exclude root layer
            # Determine sibling
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                directions.append(1)  # sibling is on the right
            else:
                sibling_index = current_index - 1
                directions.append(0)  # sibling is on the left

            if sibling_index < len(layer):
                proof.append(layer[sibling_index])
            else:
                proof.append(layer[current_index])  # duplicate self

            current_index = current_index // 2

        return proof, directions

    def verify_proof(self, leaf_hash: bytes, proof: List[bytes],
                     index: int) -> bool:
        """
        Verify a Merkle proof locally (mirrors on-chain verification).

        Args:
            leaf_hash: The hash of the leaf to verify
            proof: List of sibling hashes
            index: The index of the leaf in the tree
        """
        computed = leaf_hash

        for sibling in proof:
            if index % 2 == 0:
                computed = keccak256_pair(computed, sibling)
            else:
                computed = keccak256_pair(sibling, computed)
            index = index // 2

        return computed == self.root

    def get_stats(self) -> dict:
        """Return tree statistics for the paper's evaluation section."""
        return {
            "num_leaves": len(self.original_leaves),
            "num_leaves_padded": len(self.leaves),
            "depth": self.depth,
            "num_layers": len(self.layers),
            "root_hex": self.root_hex,
            "proof_size_per_leaf": self.depth,  # number of hashes
            "proof_bytes_per_leaf": self.depth * 32,  # bytes
        }


# ======================== Performance Benchmarking ========================

def benchmark_tree(num_leaves: int, num_verify: int = 100) -> dict:
    """
    Benchmark Merkle tree construction and verification.
    Used for generating Table 1 in the paper.
    """
    import random

    # Generate random leaves
    leaves = [sha256_hash(f"decision_{i}_{random.random()}")
              for i in range(num_leaves)]

    # Benchmark construction
    t0 = time.perf_counter()
    tree = MerkleTree(leaves)
    build_time = time.perf_counter() - t0

    # Benchmark proof generation
    indices = [random.randint(0, num_leaves - 1) for _ in range(num_verify)]

    t0 = time.perf_counter()
    proofs = [tree.get_proof(i) for i in indices]
    proof_gen_time = (time.perf_counter() - t0) / num_verify

    # Benchmark verification
    t0 = time.perf_counter()
    for i, (proof, _) in zip(indices, proofs):
        tree.verify_proof(leaves[i], proof, i)
    verify_time = (time.perf_counter() - t0) / num_verify

    return {
        "num_leaves": num_leaves,
        "build_time_ms": round(build_time * 1000, 2),
        "proof_gen_time_us": round(proof_gen_time * 1e6, 2),
        "verify_time_us": round(verify_time * 1e6, 2),
        "tree_depth": tree.depth,
        "proof_size_bytes": tree.depth * 32,
        "root": tree.root_hex,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("ChainMind Merkle Tree — Performance Benchmark")
    print("=" * 60)

    sizes = [10, 50, 100, 500, 1000, 5000, 10000, 50000]

    print(f"\n{'Leaves':>8} | {'Build(ms)':>10} | {'Proof(μs)':>10} | "
          f"{'Verify(μs)':>10} | {'Depth':>5} | {'Proof(B)':>8}")
    print("-" * 72)

    for n in sizes:
        stats = benchmark_tree(n)
        print(f"{stats['num_leaves']:>8} | "
              f"{stats['build_time_ms']:>10.2f} | "
              f"{stats['proof_gen_time_us']:>10.2f} | "
              f"{stats['verify_time_us']:>10.2f} | "
              f"{stats['tree_depth']:>5} | "
              f"{stats['proof_size_bytes']:>8}")

    print("\nDone. These results go into Table 1 of the paper.")
