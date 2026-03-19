# ChainMind

**Blockchain-Based Accountability Framework for LLM-Powered DeFi Agents**

Submitted to [Nanyang Blockchain Conference 2026 (NBC'26)](https://www.ntu.edu.sg/cctf/cctf-community/2026-nanyang-blockchain-conference), NTU Singapore.

## Overview

ChainMind provides an on-chain accountability layer for LLM-powered DeFi agents. It records cryptographic commitments of agent decisions (input, output, and model metadata hashes) using Merkle trees for gas-efficient batch submission, with O(log n) single-decision verification.

## Architecture

| Layer | Component | Description |
|-------|-----------|-------------|
| Agent | Ollama (qwen2.5:7b) | Local LLM generating DeFi risk assessments |
| Commitment | SHA-256 + Merkle Tree | Cryptographic hashing and batch commitment |
| Blockchain | AgentAccountability.sol | Sepolia smart contract for on-chain storage |
| Verification | Merkle Proof | O(log n) per-decision tamper detection |

## Smart Contract

- **Address**: [`0xD134842c3a255C7f70873EAD16A26BB4f728a423`](https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423)
- **Network**: Ethereum Sepolia Testnet
- **Verified**: Sourcify / Blockscout / Routescan

## Reproduce
```bash
# 1. Setup
conda create -n chainmind python=3.11 -y
conda activate chainmind
pip install -r requirements.txt

# 2. Run pipeline (mock mode, no LLM needed)
cd scripts
python pipeline.py --mock -n 10

# 3. Run pipeline (with local LLM)
ollama serve          # in another terminal
ollama pull qwen2.5:7b
python pipeline.py -n 10

# 4. Performance benchmarks
python merkle_tree.py
```

## Project Structure
```
ChainMind/
├── contracts/
│   └── AgentAccountability.sol   # Solidity smart contract
├── scripts/
│   ├── merkle_tree.py            # Merkle tree + benchmarks
│   ├── agent_simulator.py        # LLM agent simulator (10 DeFi scenarios)
│   └── pipeline.py               # End-to-end pipeline
├── docs/
│   └── deployment_info.txt       # On-chain deployment records
├── requirements.txt
└── README.md
```

## Author

**Kefan Liu** — MSc Blockchain Technology, Nanyang Technological University (NTU), Singapore

## License

MIT
