# ChainMind 论文 Overleaf 编译教程

## 操作步骤（5分钟搞定）

### Step 1：打开 Overleaf
1. 浏览器访问 **https://www.overleaf.com**
2. 登录你的账号（没有就免费注册一个）

### Step 2：创建新项目
1. 点击左上角绿色按钮 **New Project**
2. 选择 **Upload Project**
3. 把我给你的 `ChainMind_NBC26.tex` 文件直接拖进去上传
4. 项目自动创建并打开

### Step 3：编译
1. 点击右上角绿色按钮 **Recompile**
2. 等几秒钟，右侧就会显示论文 PDF 预览
3. 如果编译成功，你就能看到完整排版的论文了

### Step 4：添加图片（可选）
1. 点击左侧文件栏上方的 **上传** 图标
2. 上传 `fig_gas_comparison.png`、`fig_performance.png`、`fig_proof_size.png`
3. 在 .tex 文件中把 Figure 1 的占位表格替换成 `\includegraphics` 命令

### Step 5：下载 PDF
1. 点击右上角 **Download PDF** 按钮
2. 保存到本地

### Step 6：提交
1. 访问 **https://nbc26.hotcrp.com**
2. 注册/登录
3. 点 **New Submission**
4. 上传 PDF
5. 填写 Title、Abstract、Authors 信息
6. 提交！

## 注意事项
- Overleaf 自带 `acmart.cls`，不需要手动安装
- 编译器确认选的是 **pdfLaTeX**（默认就是）
- 如果报错，点击 Logs 查看具体错误信息
