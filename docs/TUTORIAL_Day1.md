# ChainMind 保姆级教程 — Week 1 Day 1

> **目标**：在你的 MacBook 上跑通完整 pipeline（Agent → Merkle → 链上部署）
>
> **预计时间**：2-3小时
>
> **前置条件**：你已有 conda、Ollama (qwen2.5:7b)、MetaMask (Sepolia)、Chrome 浏览器

---

## 第一阶段：项目初始化（15分钟）

### Step 1.1 — 创建项目目录

打开 Terminal（按 `Cmd + Space` 搜索 "Terminal"），逐行输入：

```bash
cd ~/Projects
mkdir -p ChainMind/{contracts,scripts,data,docs}
cd ChainMind
```

### Step 1.2 — 创建 conda 环境

```bash
conda create -n chainmind python=3.11 -y
conda activate chainmind
```

每次打开新 Terminal 都要先运行 `conda activate chainmind`。

### Step 1.3 — 安装 Python 依赖

```bash
pip install web3 eth-abi requests matplotlib pandas
```

验证安装：

```bash
python -c "from web3 import Web3; print('web3 version:', Web3.__version__)"
```

应该打印类似 `web3 version: 7.x.x`。

### Step 1.4 — 把代码文件放到对应位置

把我给你的文件放到以下位置：

```
~/Projects/ChainMind/
├── contracts/
│   └── AgentAccountability.sol    ← 智能合约
├── scripts/
│   ├── merkle_tree.py             ← Merkle树实现
│   ├── agent_simulator.py         ← LLM Agent模拟器
│   └── pipeline.py                ← 主流水线
├── data/                          ← 实验数据输出目录
└── docs/                          ← 论文文档
```

---

## 第二阶段：运行 Agent + Merkle Pipeline（30分钟）

### Step 2.1 — 确认 Ollama 在运行

打开**另一个** Terminal 窗口，运行：

```bash
ollama serve
```

如果看到 "Listening on 127.0.0.1:11434"，说明已启动。如果显示端口已被占用，说明 Ollama 已经在后台运行了，直接关掉这个窗口即可。

验证模型可用：

```bash
ollama list
```

应该看到 `qwen2.5:7b` 在列表中。如果没有：

```bash
ollama pull qwen2.5:7b
```

### Step 2.2 — 先用 Mock 模式测试（不需要 Ollama）

回到你的主 Terminal（确认 `chainmind` 环境已激活）：

```bash
cd ~/Projects/ChainMind/scripts
python pipeline.py --mock -n 10
```

你应该看到：

```
STEP 1: Generating LLM agent decisions
...
STEP 2: Building Merkle tree
  Leaves:     10
  Tree depth: 4
  Root:       0x...
...
STEP 5: Performance benchmarks (for paper Table 1)
...
PIPELINE COMPLETE
```

检查输出文件：

```bash
ls -la ../data/
```

应该有 4 个 JSON 文件。

### Step 2.3 — 用 Ollama 真实 LLM 运行

```bash
python pipeline.py -n 10
```

这次会真的调用 qwen2.5:7b 来分析每个 DeFi 场景。每个 decision 大约需要 5-15 秒（取决于你的 Mac 配置）。

运行成功后，打开 `data/decisions.json` 看看：

```bash
cat ../data/decisions.json | python -m json.tool | head -30
```

你会看到每条 decision 的 input prompt、LLM response、以及对应的 SHA-256 哈希。

### Step 2.4 — 运行大规模性能测试（论文实验数据）

```bash
python merkle_tree.py
```

这会生成 Table 1 的原始数据（从 10 到 50,000 条 decisions 的构建/验证时间）。

**把终端输出截图保存！** 这就是论文中的实验数据。

---

## 第三阶段：部署智能合约到 Sepolia（45分钟）

### Step 3.1 — 打开 Remix IDE

1. 打开 Chrome 浏览器
2. 访问 **https://remix.ethereum.org**
3. 等待加载完成

### Step 3.2 — 创建合约文件

1. 在左侧文件浏览器中，点击 `contracts` 文件夹
2. 右键 → **New File**
3. 文件名输入：`AgentAccountability.sol`
4. 把我给你的 `AgentAccountability.sol` 全部内容复制粘贴进去

### Step 3.3 — 编译合约

1. 点击左侧边栏的 **Solidity Compiler** 图标（第二个图标，看起来像一个 "S"）
2. Compiler 版本选择 **0.8.20** 或更高（确保 ≥ 0.8.20）
3. 点击蓝色按钮 **Compile AgentAccountability.sol**
4. 编译成功后，按钮旁边会出现一个绿色 ✓

如果报错，检查 Solidity 版本是否选对了。

### Step 3.4 — 连接 MetaMask

1. 点击左侧边栏的 **Deploy & Run Transactions** 图标（第三个图标，看起来像一个以太坊标志）
2. **ENVIRONMENT** 下拉菜单选择 **Injected Provider - MetaMask**
3. MetaMask 弹窗出现 → 点击 **Connect**
4. 确认 MetaMask 顶部显示 **Sepolia Test Network**

如果没有 Sepolia 测试 ETH，去水龙头领取：
- https://www.alchemy.com/faucets/ethereum-sepolia
- https://cloud.google.com/application/web3/faucet/ethereum/sepolia

### Step 3.5 — 部署合约

1. 确认 **CONTRACT** 下拉菜单显示 `AgentAccountability`
2. 点击橙色 **Deploy** 按钮
3. MetaMask 弹出交易确认 → 点击 **Confirm**
4. 等待 15-30 秒，底部控制台显示绿色 ✓

### Step 3.6 — 记录合约地址

1. 部署成功后，左侧 **Deployed Contracts** 出现你的合约
2. 点击合约名称旁边的 **复制** 图标
3. **重要：把合约地址保存下来！** 格式类似 `0x1234...abcd`

打开 Terminal 记录一下：

```bash
echo "Contract Address: 0x你的合约地址" > ~/Projects/ChainMind/docs/deployment_info.txt
echo "Network: Sepolia" >> ~/Projects/ChainMind/docs/deployment_info.txt
echo "Deployed: $(date)" >> ~/Projects/ChainMind/docs/deployment_info.txt
```

### Step 3.7 — 在 Etherscan 查看合约

打开：`https://sepolia.etherscan.io/address/你的合约地址`

截图保存 — 论文需要这个作为证据。

---

## 第四阶段：链上提交 Merkle Root（30分钟）

### Step 4.1 — 获取 Merkle Root

打开 `data/remix_submission.json`：

```bash
cat ~/Projects/ChainMind/data/remix_submission.json | python -m json.tool
```

找到 `submitBatch` 部分：

```json
{
  "submitBatch": {
    "_merkleRoot": "0xabcdef...",
    "_batchSize": 10,
    "_modelId": "qwen2.5:7b"
  }
}
```

### Step 4.2 — 在 Remix 调用 submitBatch

1. 回到 Remix IDE
2. 展开 **Deployed Contracts** 下面的合约
3. 找到 **submitBatch** 函数（橙色按钮）
4. 填入参数：
   - `_merkleRoot`: 粘贴 remix_submission.json 中的 merkleRoot 值
   - `_batchSize`: 输入 `10`
   - `_modelId`: 输入 `qwen2.5:7b`
5. 点击 **transact**
6. MetaMask 弹窗 → 点击 **Confirm**
7. 等待交易确认

### Step 4.3 — 验证提交成功

在 Remix 中调用查询函数：

1. 点击 **batchCount**（蓝色按钮） → 应该返回 `1`
2. 点击 **getBatch** → 输入 `0` → 点击 call
3. 应该看到你的 merkleRoot、batchSize、时间戳等

### Step 4.4 — 测试单条决策验证

1. 从 `remix_submission.json` 中复制 `verifyDecision_example` 的数据
2. 在 Remix 中找到 **verifyDecision** 函数
3. 填入：
   - `_batchId`: `0`
   - `_leafHash`: 粘贴对应的值
   - `_proof`: 粘贴 proof 数组（格式：`["0xabc...","0xdef..."]`）
   - `_index`: `0`
4. 点击 **call**
5. 返回 `true` → 验证成功！

### Step 4.5 — 测试个别决策提交

1. 从 `remix_submission.json` 的 `individual_decisions` 部分
2. 找到第一条的 `commitDecision` 数据
3. 在 Remix 中调用 **commitDecision**，填入三个 hash
4. MetaMask 确认交易
5. 调用 **decisionCount** 验证计数增加

### Step 4.6 — 记录所有交易哈希

每次交易后，在 Remix 底部控制台点击交易记录，复制 **Transaction Hash**。

```bash
# 把所有 TX hash 记录下来
cat >> ~/Projects/ChainMind/docs/deployment_info.txt << 'EOF'

Transaction Hashes:
- Deploy:         0x...
- submitBatch:    0x...
- commitDecision: 0x...
EOF
```

---

## 第五阶段：Gas 成本分析实验（30分钟）

### Step 5.1 — 收集 Gas 数据

在 Sepolia Etherscan 上查看每笔交易的 Gas Used：

| 操作 | Gas Used | 说明 |
|------|----------|------|
| Deploy | ~______ | 合约部署 |
| commitDecision (单条) | ~______ | 单条决策提交 |
| submitBatch (10条) | ~______ | 批量10条 Merkle root |
| verifyDecision (链上) | ~______ | 只读验证（0 gas，但记录 computation） |

### Step 5.2 — 多批次 Gas 对比实验

重复运行 pipeline 生成不同规模的 batch：

```bash
cd ~/Projects/ChainMind/scripts

# 50条 decisions
python pipeline.py --mock -n 50 -o ../data/batch_50
# 复制 merkleRoot → Remix → submitBatch → 记录 Gas

# 100条
python pipeline.py --mock -n 100 -o ../data/batch_100

# 500条
python pipeline.py --mock -n 500 -o ../data/batch_500

# 1000条
python pipeline.py --mock -n 1000 -o ../data/batch_1000
```

每次都在 Remix 上提交对应的 Merkle root，记录 Gas。

**关键发现预览**：无论 batch 中有多少条 decisions，submitBatch 的 gas 几乎相同（因为链上只存一个 bytes32 root），而 commitDecision × N 的 gas 线性增长。这就是你的 Figure 3 的核心数据。

---

## Day 1 检查清单

完成以上步骤后，你应该有：

- [ ] `chainmind` conda 环境配好
- [ ] 4个 Python 脚本能正常运行
- [ ] `data/` 目录下有 decisions.json, merkle_proofs.json, benchmarks.json
- [ ] 智能合约部署到 Sepolia（有合约地址）
- [ ] 至少一个 submitBatch 交易成功（有 TX hash）
- [ ] 至少一个 commitDecision 交易成功
- [ ] verifyDecision 返回 true
- [ ] Gas 数据已记录
- [ ] 所有截图保存在 docs/ 文件夹

---

## 遇到问题？

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: No module named 'web3'` | 确认运行了 `conda activate chainmind` |
| Ollama 连接失败 | 打开新 Terminal 运行 `ollama serve` |
| MetaMask 没有 Sepolia ETH | 去水龙头：alchemy.com/faucets/ethereum-sepolia |
| Remix 编译报错 | 确认 Compiler 版本选 0.8.20+ |
| submitBatch 交易失败 | 检查 merkleRoot 格式是否以 0x 开头，且是 66 字符 |
| verifyDecision 返回 false | 确认 proof 数组格式正确，leafHash 和 index 对应 |

---

## 明天的计划 (Day 2)

- 完善 Gas 对比实验数据（5个不同 batch size）
- 用 matplotlib 生成论文图表
- 开始写 System Architecture section 的配图
