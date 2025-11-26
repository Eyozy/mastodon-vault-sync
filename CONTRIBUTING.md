# 🤝 贡献指南

欢迎为 Mastodon Vault Sync 项目贡献你的力量！无论是报告问题、提出建议还是提交代码，你的贡献都将帮助我们不断改进和完善这个项目。

## 🐛 报告问题

如果你在使用过程中遇到任何问题，请通过以下方式提交 Issue：

### 1. 检查现有 Issue
在创建新 Issue 之前，请先搜索 [现有问题](https://github.com/Eyozy/mastodon-vault-sync/issues)，确保你遇到的问题尚未被报告。

### 2. 创建新 Issue
如果问题未被报告，请点击 "New Issue" 按钮并提供以下信息：
- **清晰的标题**：简要描述问题
- **详细的描述**：
  - 问题的具体表现
  - 完整的重现步骤
  - 期望的行为
  - 实际发生的行为
  - 错误日志（如果有）
  - 环境信息：操作系统、Python 版本、项目版本等

## 💡 功能建议

如果你有新的功能想法或改进建议，欢迎提交 Feature Request：

### 1. 思考以下问题
- 这个功能是否符合项目的整体目标？
- 是否有其他方式可以实现相同的目标？
- 这个功能对其他用户是否有价值？

### 2. 提交建议
- 使用清晰的标题和详细的描述
- 解释功能的用途和好处
- 如果可能，提供实现方案或伪代码示例
- 讨论功能的潜在影响和兼容性

## 🛠️ 代码贡献

### 开发环境设置

#### 1. Fork 仓库
点击 GitHub 页面右上角的 "Fork" 按钮，将仓库复制到你的 GitHub 账号下。

#### 2. 克隆到本地
```bash
git clone https://github.com/你的用户名/mastodon-vault-sync.git
cd mastodon-vault-sync
```

#### 3. 设置上游仓库
```bash
git remote add upstream https://github.com/Eyozy/mastodon-vault-sync.git
```

#### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 开发流程

#### 1. 更新本地仓库
在开始开发前，确保你的本地仓库与上游仓库同步：
```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

#### 2. 创建功能分支
```bash
# 新功能开发
git checkout -b feature/功能名称
# 问题修复
git checkout -b fix/问题描述
```

#### 3. 测试
- 为新功能或修复添加相应的测试
- 确保所有现有测试通过

#### 4. 提交更改
```bash
git add .
git commit -m '类型: 简短描述'
```

**提交类型建议：**
- `feat`: 新增功能
- `fix`: 修复问题
- `docs`: 文档更新
- `refactor`: 代码重构（不影响功能）
- `chore`: 构建或工具配置更新

#### 5. 推送分支
```bash
git push origin 分支名称
```

#### 6. 创建 Pull Request
- 访问你的 GitHub 仓库页面
- 点击 "New Pull Request" 按钮
- 选择要合并的分支
- 填写 PR 描述，说明更改内容和原因
- 确保 PR 与目标分支没有冲突

## 📚 文档贡献

文档是项目的重要组成部分！你可以贡献：

### 改进指南
- 修正拼写错误和语法问题
- 改进文档结构和可读性
- 添加更详细的使用说明
- 补充示例代码

### 翻译
- 将文档翻译成其他语言
- 确保翻译准确、流畅

## 🎓 行为准则

请遵守项目的行为准则，保持友好、尊重的交流方式。

## 💬 交流方式

- 项目 Issue 页面