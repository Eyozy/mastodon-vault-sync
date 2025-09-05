# 🤝 贡献指南

欢迎为 Mastodon Vault Sync 项目贡献您的力量！无论是报告问题、提出建议还是提交代码，您的贡献都非常宝贵。

## 🐛 报告问题

如果您在使用过程中遇到任何问题，请通过以下方式报告：

1.  访问项目的 [Issues 页面](https://github.com/Eyozy/mastodon-vault-sync/issues)
2.  点击 "New Issue" 按钮
3.  详细描述您遇到的问题，包括：
    - 问题的具体表现
    - 重现步骤
    - 期望的行为
    - 实际发生的行为
    - 相关的环境信息（操作系统、Python 版本等）

## 💡 功能建议

如果您有新的功能想法或改进建议，欢迎：

1.  在 Issues 页面创建新的功能请求
2.  详细描述您的建议
3.  解释为什么这个功能对项目有价值
4.  如果可能，提供实现方案或伪代码

## 🛠️ 代码贡献

### 开发环境设置

1.  **Fork 仓库**
    - 点击 GitHub 页面右上角的 "Fork" 按钮
    - 将仓库复制到您的 GitHub 账号下

2.  **克隆到本地**
    ```bash
    git clone https://github.com/您的用户名/mastodon-vault-sync.git
    cd mastodon-vault-sync
    ```

3.  **设置上游仓库**
    ```bash
    git remote add upstream https://github.com/Eyozy/mastodon-vault-sync.git
    ```

4.  **创建虚拟环境（推荐）**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # 或
    venv\Scripts\activate     # Windows
    ```

5.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

### 开发流程

1.  **创建功能分支**
    ```bash
    git checkout -b feature/您的功能名称
    ```

2.  **进行开发**
    - 编写代码
    - 添加必要的测试
    - 更新相关文档

3.  **提交更改**
    ```bash
    git add .
    git commit -m '添加：描述您的更改'
    ```

4.  **推送分支**
    ```bash
    git push origin feature/您的功能名称
    ```

5.  **创建 Pull Request**
    - 访问您的 GitHub 仓库页面
    - 点击 "New Pull Request"
    - 填写 PR 描述，说明您的更改内容和原因

### 代码规范

- 遵循 PEP 8 Python 编码规范
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串
- 保持代码简洁和可读性

### 测试要求

- 新功能应包含相应的测试
- 确保所有测试通过
- 测试覆盖率应保持在合理水平

## 📚 文档贡献

文档改进同样重要！您可以：

- 修正拼写错误和语法问题
- 改进文档结构和可读性
- 添加使用示例
- 翻译文档到其他语言
