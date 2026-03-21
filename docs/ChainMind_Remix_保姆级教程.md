# ChainMind Remix 保姆级教程

> 目标：在 Remix IDE 上完成 3 笔 commitDecision + 1 笔 verifyDecision + 1 笔篡改检测
> 预计时间：15-20 分钟
> 前置条件：MetaMask 已安装、Sepolia 有测试 ETH

---

## 第一步：打开 Remix 并连接钱包

1. 打开浏览器，访问 **https://remix.ethereum.org**
2. 确认 MetaMask 已安装并且切换到 **Sepolia 测试网络**：
   - 点击 MetaMask 狐狸图标
   - 点击顶部网络下拉菜单
   - 选择 **Sepolia test network**
   - 如果看不到 Sepolia，点击 "Show test networks" 开关打开

---

## 第二步：连接已部署的合约

因为合约已经部署好了，我们不需要重新部署，只需要"连接"它。

1. 在 Remix 左侧边栏，点击第 4 个图标 **"Deploy & Run Transactions"**（图标像一个带箭头的以太坊标志）

2. 在顶部 **ENVIRONMENT** 下拉菜单中，选择：
   **"Injected Provider - MetaMask"**
   - MetaMask 会弹出一个窗口要求连接，点 **"连接/Connect"**
   - 连接后你应该能看到你的钱包地址 `0x36c6...f82c`

3. 现在需要加载合约的 ABI。有两种方式：

   **方式 A（推荐）— 从 Etherscan 拉取：**
   - 在左侧边栏点击第 3 个图标 **"Solidity Compiler"**（图标像字母 S）
   - 在左侧文件浏览器中打开 `contracts/AgentAccountability.sol`
   - 如果文件不在，就新建一个：
     - 点击文件浏览器最上面的 📄 图标（New File）
     - 命名为 `AgentAccountability.sol`
     - 把合约代码粘贴进去
   - 点击 **"Compile AgentAccountability.sol"** 蓝色按钮
   - 等待编译完成（出现绿色勾 ✅）

4. 回到 **"Deploy & Run Transactions"** 面板（左侧第 4 个图标）

5. 在 **CONTRACT** 下拉菜单中，选择 **"AgentAccountability"**

6. **不要点 Deploy！** 而是找到下面的 **"At Address"** 输入框：
   - 在输入框中粘贴合约地址：
   ```
   0xD134842c3a255C7f70873EAD16A26BB4f728a423
   ```
   - 点击 **"At Address"** 蓝色按钮

7. 成功后，在页面下方 **"Deployed Contracts"** 区域会出现你的合约，可以展开看到所有函数

---

## 第三步：先验证一下合约状态

在做交易之前，先确认合约状态正确。

1. 在 **Deployed Contracts** 区域，展开你的合约（点击合约名称左边的三角形 ▶）

2. 你会看到一堆蓝色按钮（view 函数，不花 gas）和橙色按钮（write 函数，花 gas）

3. 点击蓝色按钮 **`batchCount`** → 应该返回 `1`（说明之前的 submitBatch 成功了）

4. 点击蓝色按钮 **`decisionCount`** → 应该返回 `0`（还没做过 commitDecision）

5. 点击蓝色按钮 **`owner`** → 应该返回你的钱包地址 `0x36c6...`

如果这些都对，说明合约连接正确，继续下一步！

---

## 第四步：commitDecision × 3（单条提交，收集 gas 数据）

我们要提交 3 条独立的决策，记录每笔的 gas 消耗，用于论文中与 submitBatch 的 gas 对比。

### 4.1 提交 Decision #1（Uniswap V3）

1. 找到橙色按钮 **`commitDecision`**，点击左边的三角形 ▶ 展开它

2. 你会看到 3 个输入框：
   - `_inputHash (bytes32)`
   - `_outputHash (bytes32)`
   - `_modelHash (bytes32)`

3. 分别填入以下值：

   **_inputHash:**
   ```
   0xad335dcf6281c844b52d2faf98743443819fe4488bbba852fc19262df579b993
   ```

   **_outputHash:**
   ```
   0x98cdbcda63efb5b9276e4e4811661e0c4836dd1b4306c53ce8afc271bc6478eb
   ```

   **_modelHash:**
   ```
   0x956493cf854d6f330cace75086592549f6073bd47034227f11880159f31a31ca
   ```

4. 点击橙色的 **`transact`** 按钮

5. MetaMask 弹出确认窗口：
   - 看一眼 Gas Fee 估算（大概 0.0001 ETH 左右）
   - 点 **"确认/Confirm"**

6. 等待交易完成（Remix 底部控制台会显示绿色勾 ✅）

7. **📝 记录数据！** 点击 Remix 底部控制台中的交易记录，展开看到：
   - `transaction hash`: 记下来
   - `gas`: 记下来

   或者去 Etherscan 查：
   - 打开 https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423
   - 找到你刚才的交易，点进去
   - 记录 **Gas Used By Transaction** 这个数字

### 4.2 提交 Decision #2（Aave V3）

重复上面的步骤，但换成这组数据：

**_inputHash:**
```
0xa064bbaf7c8b61da7ee0e0c41a991f13b1b6f41b7bfdc2612b603f5f29628cbc
```

**_outputHash:**
```
0x09a7f6d237e010b804c54b5d490fe9b1490913598fffb4777031f08e587d3d7b
```

**_modelHash:**
```
0x956493cf854d6f330cace75086592549f6073bd47034227f11880159f31a31ca
```

点 transact → MetaMask 确认 → 记录 gas

### 4.3 提交 Decision #3（Compound V3）

**_inputHash:**
```
0x476f6e077b4fce24a8cca633de1a9d502060429ad57f9034b3f3662e41122fc7
```

**_outputHash:**
```
0x6bad62b396f8a4ba5a3e979219cfac5dd1edd5c110627bfbdeab0c9702584e71
```

**_modelHash:**
```
0x956493cf854d6f330cace75086592549f6073bd47034227f11880159f31a31ca
```

点 transact → MetaMask 确认 → 记录 gas

### 4.4 验证提交成功

点击蓝色按钮 **`decisionCount`** → 应该返回 `3`

---

## 第五步：verifyDecision（Merkle proof 链上验证）

这是论文的核心演示——证明某条决策确实在之前提交的 Merkle batch 中。

1. 找到蓝色按钮 **`verifyDecision`**（注意是蓝色！因为这是 view 函数，不花 gas）

2. 展开它，你会看到 4 个输入框

3. **先确认 batchId**：
   - 点击蓝色按钮 `batchCount` 查看返回值
   - 如果返回 `1`，说明只有 1 个 batch，它的 ID 是 `0`
   - 所以 _batchId 填 `0`

4. 填入以下值：

   **_batchId:**
   ```
   0
   ```

   **_leafHash:**
   ```
   0x7a889f57283e01d8616b9174dfab092bc60675bce463ca74682ac283ff7acdda
   ```

   **_proof (bytes32[]):**
   ```
   ["0x28789bbd908998aec7ea54546412c937fd54631acf4fcb91f73b962863f3f072","0xa4859efa1bdb4b8ec16f202134fbb310b2470fae1702077b66f13c98b7516a55","0xea70ba9bc81aebb66fa5c0f7206827f39733a9264d1289e08bb24353c17499a8","0x4cbbf5c207a94bef1b2f845fd9d7c512eb1e4c6b820b2ad63e0dea57a1a0b49a"]
   ```

   **_index:**
   ```
   0
   ```

5. 点击蓝色的 **`call`** 按钮（不是 transact，因为是 view 函数）

6. 底部应该返回：**`bool: true`** ✅

   → 这意味着 Decision #0 的确存在于我们之前提交的 Merkle batch 中！

---

## 第六步：篡改检测演示（论文亮点！）

现在我们演示：如果有人篡改了决策内容，系统能检测到。

做法：把 leafHash 的最后两位从 `da` 改成 `ff`，其他完全不变。

1. 还是在 **`verifyDecision`** 函数

2. 填入以下值（注意 leafHash 最后两位变了！）：

   **_batchId:**
   ```
   0
   ```

   **_leafHash（篡改版，最后两位 da → ff）:**
   ```
   0x7a889f57283e01d8616b9174dfab092bc60675bce463ca74682ac283ff7acdff
   ```

   **_proof（和上面完全一样）:**
   ```
   ["0x28789bbd908998aec7ea54546412c937fd54631acf4fcb91f73b962863f3f072","0xa4859efa1bdb4b8ec16f202134fbb310b2470fae1702077b66f13c98b7516a55","0xea70ba9bc81aebb66fa5c0f7206827f39733a9264d1289e08bb24353c17499a8","0x4cbbf5c207a94bef1b2f845fd9d7c512eb1e4c6b820b2ad63e0dea57a1a0b49a"]
   ```

   **_index:**
   ```
   0
   ```

3. 点击 **`call`**

4. 底部应该返回：**`bool: false`** ❌

   → 仅仅修改了 1 个字节，验证就失败了！这就是 Merkle 树的篡改检测能力！

---

## 第七步：记录所有数据

请把以下数据发给我，我帮你更新论文图表：

```
commitDecision #1  TX Hash: 0x...  Gas Used: ____
commitDecision #2  TX Hash: 0x...  Gas Used: ____
commitDecision #3  TX Hash: 0x...  Gas Used: ____
verifyDecision     结果: true / false
篡改检测           结果: true / false
```

另外，之前 submitBatch 的 gas 也需要：
- 去 Etherscan 找之前那笔 submitBatch 交易
- 链接：https://sepolia.etherscan.io/address/0xD134842c3a255C7f70873EAD16A26BB4f728a423
- 找到 "Submit Batch" 那笔，点进去记录 Gas Used

---

## 常见问题

**Q: MetaMask 没弹出确认窗口？**
A: 检查 MetaMask 是否锁定了。点击 MetaMask 图标，输入密码解锁。

**Q: 交易失败（红色叉）？**
A: 可能原因：
- Sepolia ETH 不够 → 去 https://sepoliafaucet.com 领取
- 网络拥堵 → 等一会儿再试
- 连接的不是部署合约的那个钱包账户 → 在 MetaMask 切换账户

**Q: "Agent not registered" 错误？**
A: 说明你当前的 MetaMask 账户不是部署合约的那个。切换到 `0x36c6...f82c` 这个账户。

**Q: verifyDecision 返回 false（应该是 true 的时候）？**
A: 检查 batchId 是否正确。点 `batchCount`，如果返回 1，batchId 就是 0。

**Q: 在哪里看 Gas Used？**
A: 两种方式：
1. Remix 底部控制台 → 展开交易 → 找 "gas" 字段
2. Etherscan → 点击 TX hash → "Gas Used By Transaction"

---

> 做完后把数据发给我，我立刻帮你：
> 1. 更新 Fig 5 为实测 gas 数据版
> 2. 生成论文 Table 2 (Gas Cost Comparison)
> 3. 开始论文写作！
