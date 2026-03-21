#!/usr/bin/env python3
"""
ChainMind — 准备 Remix IDE 提交参数
读取 pipeline 输出，生成可直接粘贴到 Remix 的参数格式

Usage:
    conda activate chainmind
    cd ~/Projects/ChainMind/scripts
    python prepare_remix_params.py
"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def load_json(filename):
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"❌ 文件不存在: {filepath}")
        print(f"   请先运行 pipeline: python pipeline.py --mock -n 10")
        return None
    with open(filepath) as f:
        return json.load(f)

def format_bytes32(hex_str):
    """确保 bytes32 格式正确 (0x + 64 hex chars)"""
    if not hex_str.startswith("0x"):
        hex_str = "0x" + hex_str
    # pad to 66 chars (0x + 64)
    return hex_str.ljust(66, '0')

def prepare_commit_decision_params(decisions):
    """
    准备 commitDecision 参数 — 选3条用于 gas 对比实验
    函数签名: commitDecision(bytes32 inputHash, bytes32 outputHash, bytes32 modelHash)
    """
    print("=" * 70)
    print("📝 commitDecision 参数 — 单条提交 (选3条做 gas 对比)")
    print("=" * 70)
    print()
    print("在 Remix 中:")
    print("1. 打开 AgentAccountability.sol")
    print("2. 在 Deploy & Run 中选择 'Injected Provider - MetaMask'")
    print("3. 在 'At Address' 输入: 0xD134842c3a255C7f70873EAD16A26BB4f728a423")
    print("4. 展开 commitDecision 函数，粘贴下面的参数")
    print()

    # 选前3条决策
    for i, decision in enumerate(decisions[:3]):
        input_hash = format_bytes32(decision.get("input_hash", decision.get("inputHash", "")))
        output_hash = format_bytes32(decision.get("output_hash", decision.get("outputHash", "")))
        model_hash = format_bytes32(decision.get("model_hash", decision.get("modelHash", "")))

        print(f"--- Decision #{i+1} (场景: {decision.get('scenario', decision.get('protocol', 'unknown'))}) ---")
        print(f"inputHash:  {input_hash}")
        print(f"outputHash: {output_hash}")
        print(f"modelHash:  {model_hash}")
        print()
        print(f"  📋 Remix 一行粘贴格式:")
        print(f'  "{input_hash}","{output_hash}","{model_hash}"')
        print()

    print("⚠️  每次提交后记录 TX hash 和 gas used!")
    print("   在 Etherscan 上查看: https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423")
    print()

def prepare_verify_decision_params(proofs, decisions):
    """
    准备 verifyDecision 参数 — 用于论文演示
    函数签名: verifyDecision(uint256 batchId, bytes32 leafHash, bytes32[] proof, uint256 index)
    """
    print("=" * 70)
    print("🔍 verifyDecision 参数 — Merkle proof 链上验证")
    print("=" * 70)
    print()
    print("batchId = 1 (第一次 submitBatch 的 ID)")
    print()

    # 如果 proofs 是 dict 格式
    if isinstance(proofs, dict):
        proof_list = proofs.get("proofs", [])
    elif isinstance(proofs, list):
        proof_list = proofs
    else:
        proof_list = []

    # 显示前3条的验证参数
    for i, proof_entry in enumerate(proof_list[:3]):
        if isinstance(proof_entry, dict):
            leaf_hash = format_bytes32(proof_entry.get("leaf_hash", proof_entry.get("leafHash", "")))
            proof = proof_entry.get("proof", proof_entry.get("siblings", []))
            index = proof_entry.get("index", proof_entry.get("leaf_index", i))
        else:
            continue

        print(f"--- Verify Decision #{i+1} ---")
        print(f"batchId:  1")
        print(f"leafHash: {leaf_hash}")
        print(f"index:    {index}")
        print()

        # 格式化 proof array for Remix
        proof_formatted = [format_bytes32(p) for p in proof]
        proof_str = "[" + ",".join(f'"{p}"' for p in proof_formatted) + "]"
        print(f"proof:    {proof_str}")
        print()
        print(f"  📋 Remix 一行粘贴格式:")
        print(f'  1,"{leaf_hash}",{proof_str},{index}')
        print()

    print("✅ 验证成功 = 返回 true → 证明该决策确实在 batch 中")
    print("❌ 验证失败 = 返回 false → 说明数据被篡改")
    print()

def prepare_tamper_detection_demo(proofs):
    """
    准备篡改检测演示参数 — 修改1个byte，验证应该 fail
    """
    print("=" * 70)
    print("🔴 篡改检测演示 — 修改 leafHash 的最后1个字节")
    print("=" * 70)
    print()

    if isinstance(proofs, dict):
        proof_list = proofs.get("proofs", [])
    elif isinstance(proofs, list):
        proof_list = proofs
    else:
        proof_list = []

    if proof_list:
        entry = proof_list[0]
        if isinstance(entry, dict):
            original = entry.get("leaf_hash", entry.get("leafHash", ""))
            original = format_bytes32(original)
            # 篡改最后一个字节
            tampered = original[:-2] + ("ff" if original[-2:] != "ff" else "00")

            proof = entry.get("proof", entry.get("siblings", []))
            index = entry.get("index", entry.get("leaf_index", 0))
            proof_formatted = [format_bytes32(p) for p in proof]
            proof_str = "[" + ",".join(f'"{p}"' for p in proof_formatted) + "]"

            print(f"原始 leafHash: {original}")
            print(f"篡改 leafHash: {tampered}")
            print()
            print(f"📋 用篡改的 hash 调用 verifyDecision:")
            print(f'  1,"{tampered}",{proof_str},{index}')
            print()
            print("预期结果: 返回 false ← 这就是篡改检测！论文 Section 5 的关键演示")

def generate_gas_recording_template():
    """
    生成 gas 数据记录模板
    """
    print()
    print("=" * 70)
    print("📊 Gas 数据记录模板 — 填入 Etherscan 查到的实际值")
    print("=" * 70)
    print()
    print("请在每次 Remix 交易后，从 Etherscan TX 详情中记录 gas:")
    print()
    print("| 操作 | TX Hash | Gas Used | Gas Price (Gwei) |")
    print("|------|---------|----------|------------------|")
    print("| commitDecision #1 | 0x... | | |")
    print("| commitDecision #2 | 0x... | | |")
    print("| commitDecision #3 | 0x... | | |")
    print("| verifyDecision #1 | 0x... | | |")
    print("| verifyDecision (tampered) | 0x... | | |")
    print()
    print("已有数据:")
    print("| submitBatch (10 decisions) | 已完成 | 查 Etherscan | |")
    print()
    print("论文 Table 2 需要的对比:")
    print("  单条提交 10 次 gas 总和  vs  submitBatch 1 次 gas")
    print("  → 证明批量提交节省 gas")

def main():
    print("🔗 ChainMind — Remix 参数准备工具")
    print(f"📁 数据目录: {DATA_DIR}")
    print()

    decisions = load_json("decisions.json")
    proofs = load_json("merkle_proofs.json")

    if decisions is None or proofs is None:
        print("\n💡 请先运行 pipeline 生成数据:")
        print("   cd ~/Projects/ChainMind/scripts")
        print("   python pipeline.py --mock -n 10")
        return

    prepare_commit_decision_params(decisions)
    prepare_verify_decision_params(proofs, decisions)
    prepare_tamper_detection_demo(proofs)
    generate_gas_recording_template()

    print()
    print("=" * 70)
    print("✅ 全部参数已准备好！按顺序在 Remix 中执行即可。")
    print("=" * 70)

if __name__ == "__main__":
    main()
