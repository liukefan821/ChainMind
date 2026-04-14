# ChainMind 项目交接文档 — NBC'26 论文冲刺

> 在新的 Claude 对话开头粘贴本文档，即可无缝继续。
> 最后更新：2026-03-20 05:20 SGT

---

## 一、项目概况

**论文标题（暂定）**：ChainMind: Blockchain-Based Accountability Framework for LLM-Powered DeFi Agents

**目标会议**：Nanyang Blockchain Conference 2026 (NBC'26)
- 时间：2026年8月21-22日，NTU Singapore
- 投稿DDL：2026年4月20日 11:59pm AoE
- 投稿网站：https://nbc26.hotcrp.com
- 格式：ACM single-column，8-25页（含参考文献），PDF
- 非盲审（可带作者信息），non-archival
- 精选论文受邀投 ACM Distributed Ledger Technologies 期刊特刊

**作者**：Kefan Liu（独立作者，NTU CCTF MSc Blockchain Technology）

**核心贡献**：设计并实现一个智能合约框架，通过链上密码学承诺记录 LLM Agent 的 DeFi 决策（input hash、output hash、model hash），使用 Merkle 树实现 gas 高效的批量提交，支持 O(log n) 单条决策验证和篡改检测。

---

## 二、系统架构（四层）

1. **Agent Layer** — 本地 LLM (Ollama qwen2.5:7b) 模拟 DeFi Agent，分析10种DeFi场景（Uniswap、Aave、Compound、MakerDAO、Curve、Lido、GMX、Pendle、Morpho、Eigenlayer），生成风险评估和交易建议
2. **Commitment Layer** — SHA-256 对 input/output/model metadata 做哈希，keccak256 构建 Merkle 树
3. **Blockchain Layer** — 智能合约 `AgentAccountability.sol` 部署在 Sepolia，支持单条提交 (commitDecision) 和批量提交 (submitBatch)
4. **Verification Layer** — 链上 verifyDecision() 函数 + 链下 proof 生成，O(log n) 验证

---

## 三、已完成的工作（Day 1 — 2026-03-20）

### 3.1 代码实现 ✅

本地项目路径：`~/Projects/ChainMind/`
Conda 环境：`chainmind` (Python 3.11)
依赖：web3, eth-abi, requests, matplotlib, pandas

文件结构：
```
~/Projects/ChainMind/
├── contracts/
│   └── AgentAccountability.sol    # Solidity 智能合约 (0.8.20+)
├── scripts/
│   ├── merkle_tree.py             # Merkle 树 + benchmark
│   ├── agent_simulator.py         # LLM Agent 模拟器 (10种DeFi场景)
│   ├── pipeline.py                # 端到端 pipeline
│   └── data/                      # pipeline 输出
│       ├── decisions.json         # 10条 agent 决策记录
│       ├── merkle_proofs.json     # 所有 Merkle proofs
│       ├── benchmarks.json        # 性能基准数据
│       └── remix_submission.json  # Remix 提交参数
├── data/                          # 额外实验数据
├── docs/
│   ├── TUTORIAL_Day1.md           # 保姆级教程
│   └── deployment_info.txt        # 部署记录
└── requirements.txt
```

### 3.2 链上部署 ✅

| 项目 | 值 |
|------|-----|
| 合约地址 | `0xD134842c3a255C7f70873EAD16A26BB4f728a423` |
| 网络 | Ethereum Sepolia Testnet |
| 部署TX | `0x6f133ed9323d9fb0f684b054b0d8813f8a61ac49f5c533218968217711b3878d` |
| 编译器 | Solidity 0.8.31, optimization runs=200 |
| 验证状态 | Sourcify ✓ / Blockscout ✓ / Routescan ✓ |
| Etherscan | https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423 |
| MetaMask 账户 | `0x36c6eb92bfabaf637aa1607ecce02e0ec952f82c` |

### 3.3 链上交易 ✅

| 操作 | 状态 | 说明 |
|------|------|------|
| Deploy | ✅ 完成 | 合约部署 + 自动验证 |
| submitBatch | ✅ 完成 | Merkle root 已上链，batchCount=1 |
| commitDecision | ❌ 待做 | 单条提交（用于 gas 对比实验） |
| verifyDecision | ❌ 待做 | 链上验证（论文演示） |

submitBatch 提交的数据：
- merkleRoot: `0x80efb2602f8ef9c51efacf840e7e817c6255b1a22937bd8aaf7aa07134887267`
- batchSize: 10
- modelId: "qwen2.5:7b"

### 3.4 性能基准数据（MacBook M系列实测） ✅

| 决策数量 | 构建时间 | 验证时间 | 树深度 | Proof大小 |
|---------|---------|---------|-------|----------|
| 10 | 0.93ms | 256μs | 4 | 128B |
| 50 | 2.70ms | 280μs | 6 | 192B |
| 100 | 4.23ms | 277μs | 7 | 224B |
| 500 | 19.6ms | 361μs | 9 | 288B |
| 1,000 | 39.8ms | 394μs | 10 | 320B |
| 5,000 | 198ms | 515μs | 13 | 416B |
| 10,000 | 392ms | 546μs | 14 | 448B |

---

## 四、待完成工作（Week 1 剩余 + Week 2-4）

### Week 1 剩余 (Mar 21-24)
- [ ] 在 Remix 上做 commitDecision × 3（收集单条提交 gas 数据）
- [ ] 在 Remix 上做 verifyDecision（验证 Merkle proof 上链）
- [ ] 用 Ollama 真实 LLM 重新跑 pipeline（替代 mock 数据）
- [ ] 跑多批次 gas 对比实验（batch size: 10/50/100/500/1000）
- [ ] 用 matplotlib 生成论文图表（Fig 1-6）

### Week 2 (Mar 25-31) — 论文写作
- [ ] Introduction（问题定义 + 3个贡献点）
- [ ] System Architecture（四层架构图 + 数据流）
- [ ] Cryptographic Core（SHA-256 + Merkle树 + 篡改检测）
- [ ] Smart Contract Design（合约结构 + gas优化策略）
- [ ] Experimental Evaluation（Table 1 性能 + Table 2 gas + 链上TX证据）
- [ ] Related Work（LLM漏洞检测红海 vs Agent问责蓝海）

### Week 3 (Apr 1-7) — 完善
- [ ] Discussion（与纯链上日志对比、局限性、EU AI Act合规性）
- [ ] Abstract + Conclusion
- [ ] ACM LaTeX 排版 (Overleaf, acmart single-column)
- [ ] 参考文献整理（20-25篇，真实DOI）

### Week 4 (Apr 8-20) — 冲刺
- [ ] 内部 proofread
- [ ] 图表美化
- [ ] 提交到 nbc26.hotcrp.com

---

## 五、关键技术细节

### 智能合约核心函数
- `commitDecision(bytes32 inputHash, bytes32 outputHash, bytes32 modelHash)` — 单条提交
- `submitBatch(bytes32 merkleRoot, uint256 batchSize, string modelId)` — 批量 Merkle root 提交
- `verifyDecision(uint256 batchId, bytes32 leafHash, bytes32[] proof, uint256 index)` — 链上 Merkle 验证
- `verifyIndividualDecision(uint256 decisionId, bytes32 inputHash, bytes32 outputHash, bytes32 modelHash)` — 单条验证

### Merkle 树设计
- 叶子哈希：keccak256(abi.encodePacked(inputHash, outputHash, modelHash))
- 内部节点：keccak256(abi.encodePacked(left, right))
- 奇数叶子：复制最后一个叶子
- 匹配 Solidity 的 keccak256(abi.encodePacked(...))

### 论文核心论点
1. LLM Agent 在 DeFi 中做决策缺乏问责机制（research gap）
2. 链上逐条记录 gas 太贵 → Merkle 批量提交解决可扩展性
3. O(log n) 验证效率 → 实际可用（10,000条只需14个hash）
4. 篡改检测100%（修改1字节即检测到）
5. 方向匹配 NBC'26 的 "Blockchain-AI integration" + "DeFi" + "Cryptographic primitives" 三个话题

### 竞争优势
- 区别于 LLM 漏洞检测红海（10+ papers in 2025-26）
- 2026年3月 arxiv survey 明确将 "agent accountability on-chain" 列为 open problem
- 有 working prototype + 链上部署证据 + 量化实验（很多竞争论文只有框架无实现）

---

## 六、环境恢复命令

```bash
# 激活环境
conda activate chainmind
cd ~/Projects/ChainMind

# 重新运行 pipeline（mock 模式）
cd scripts && python pipeline.py --mock -n 10

# 重新运行 pipeline（真实 LLM — 需要 Ollama 在运行）
ollama serve  # 在另一个 Terminal
cd scripts && python pipeline.py -n 10

# 运行性能 benchmark
python merkle_tree.py

# 查看链上合约
# https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423
```

---

*本文档由 Claude 生成，用于 ChainMind 项目跨对话续接。*
