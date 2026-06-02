# ChainMind

**A blockchain-based accountability framework for LLM-powered DeFi agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.31-363636.svg)](./contracts/AgentAccountability.sol)
[![Network](https://img.shields.io/badge/Network-Sepolia-7b3fe4.svg)](https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423)
[![Paper](https://img.shields.io/badge/Paper-NBC'26-brightgreen.svg)](./paper/ChainMind_NBC26.pdf)

> Author: **Kefan Liu** · 2026 · Submitted to NBC'26

---

## Overview

As Large Language Models are integrated into Decentralized Finance, autonomous agents now execute trades, assess risk, and manage portfolios with little human oversight. Because LLM reasoning is opaque and ephemeral, there is no tamper-evident record of *what inputs a model received, what output it produced, or which model version was responsible* for a given decision. ChainMind closes this accountability gap by recording cryptographic commitments of agent decisions on Ethereum, so that any individual decision can later be verified against an immutable on-chain root.

The central design insight is that **Merkle trees allow arbitrarily many decisions to be committed in a single on-chain transaction**, cutting cost by 88.9% relative to per-decision commits while still permitting verification of any single decision with `O(log n)` proof complexity.

## Key results

| Metric | Result |
|--------|--------|
| On-chain cost reduction (Merkle batch vs. individual commits) | **88.9%** |
| Batch submission cost | Constant, independent of batch size |
| Single-decision verification (batch of 10,000) | **546 µs** |
| Tamper detection accuracy | **100%** (a single-byte change fails verification) |
| Proof complexity | `O(log n)` |

All figures are reproducible from the public codebase; results in the paper were measured on Ethereum Sepolia.

## Architecture

ChainMind uses a four-layer design:

1. **Agent Layer** — a local LLM (Ollama, `qwen2.5:7b`) generates DeFi risk assessments across 10 protocol scenarios.
2. **Commitment Layer** — each decision is reduced to SHA-256 commitments over its inputs, outputs, and model metadata (model ID and version).
3. **Blockchain Layer** — the `AgentAccountability` smart contract stores commitments, supporting both individual decisions and Merkle-tree batch submissions.
4. **Verification Layer** — any single decision is verified on-chain via a Merkle proof in `O(log n)` time.

Leaf hashing uses SHA-256; internal nodes use `keccak256(abi.encodePacked(left, right))` to match Solidity's hashing exactly, so off-chain proofs verify against the on-chain contract without re-hashing mismatches.

## Repository structure

```
ChainMind/
├── contracts/
│   └── AgentAccountability.sol      # On-chain commitment + Merkle verification
├── scripts/
│   ├── agent_simulator.py           # LLM decision generation (Ollama / mock)
│   ├── merkle_tree.py               # MerkleTree, DecisionRecord, proof generation
│   ├── pipeline.py                  # End-to-end pipeline (generate → commit → verify)
│   ├── benchmark_extended.py        # Extended benchmarks
│   ├── generate_figures.py          # Reproduce paper figures
│   └── prepare_remix_params.py      # Helper for Remix deployment params
├── benchmark_large_scale.py         # Large-scale (up to 10k decisions) benchmark
├── paper/
│   ├── ChainMind_NBC26.pdf / .tex   # NBC'26 submission
│   └── figures/                     # fig1_architecture … fig6_tamper_detection
├── docs/
│   ├── deployment_info.txt          # Contract address, TX, verification status
│   ├── ChainMind_Handoff.md
│   └── ...                          # Remix / Overleaf tutorials
├── requirements.txt
└── LICENSE
```

## Smart contract

| Field | Value |
|-------|-------|
| Contract | `AgentAccountability` |
| Address | `0xD134842c3a255C7f70873EAD16A26BB4f728a423` |
| Network | Ethereum Sepolia |
| Deploy TX | `0x6f133ed9323d9fb0f684b054b0d8813f8a61ac49f5c533218968217711b3878d` |
| Compiler | Solidity 0.8.31 |
| Verified | Sourcify · Blockscout · Routescan |

Explorer: https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423

Core interface: `registerAgent`, `commitDecision` (individual), `submitBatch` (Merkle root), `verifyDecision` / `verifyIndividualDecision` (on-chain proof check), plus `getDecision` / `getBatch` views.

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Key dependencies: `web3>=7.0.0`, `eth-abi>=5.0.0`, `matplotlib`, `pandas`.

### 2. (Optional) Start the local LLM

The Agent Layer uses Ollama. To generate real decisions:

```bash
ollama serve
ollama pull qwen2.5:7b
```

If Ollama is unavailable, run the pipeline in mock mode (next step).

### 3. Run the end-to-end pipeline

```bash
cd scripts

# Generate 10 decisions with the local LLM, build the Merkle tree, generate proofs
python pipeline.py -n 10

# Mock mode — skip Ollama, use synthetic decisions
python pipeline.py -n 10 --mock

# Custom output directory
python pipeline.py -n 100 --mock -o data
```

The pipeline generates agent decisions, builds a Merkle tree from the decision hashes, generates a proof for every leaf, and verifies them locally before on-chain submission.

### 4. Reproduce the benchmarks and figures

```bash
# Large-scale cost / verification-time benchmark
python benchmark_large_scale.py

# Extended benchmarks
python scripts/benchmark_extended.py

# Regenerate paper figures
python scripts/generate_figures.py
```

## Reproducibility

The paper's experimental claims — 88.9% cost reduction, constant-cost batch submission, sub-millisecond verification at scale, and 100% tamper detection — are reproducible via the scripts above. The deployed contract is publicly verified (see `docs/deployment_info.txt`), so on-chain results can be independently confirmed against the live Sepolia deployment.

## Citation

```bibtex
@inproceedings{liu2026chainmind,
  title     = {ChainMind: A Blockchain-Based Accountability Framework for LLM-Powered DeFi Agents},
  author    = {Liu, Kefan},
  booktitle = {Proceedings of NBC'26},
  year      = {2026}
}
```

## License

Released under the [MIT License](./LICENSE). © 2026 Kefan Liu.
