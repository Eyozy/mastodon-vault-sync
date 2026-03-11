# 🤝 贡献指南

感谢你对 Mastodon Vault Sync 的关注！我们欢迎各种形式的贡献。

## 🐛 报告问题

在提交 Issue 前，请先[搜索现有问题](https://github.com/Eyozy/mastodon-vault-sync/issues)避免重复。

**Issue 应包含：**
- 清晰的标题和详细描述
- 完整的重现步骤
- 期望行为 vs 实际行为
- 错误日志（如有）
- 环境信息：操作系统、Python 版本、项目版本

## 💡 功能建议

提交 Feature Request 时，请说明：
- 功能的用途和价值
- 可能的实现方案
- 对现有功能的影响

## 🛠️ 代码贡献

### 开发环境设置

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/你的用户名/mastodon-vault-sync.git
cd mastodon-vault-sync

# 2. 添加上游仓库
git remote add upstream https://github.com/Eyozy/mastodon-vault-sync.git
```

```bash
# 3. macOS / Linux: 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

```powershell
# 3. Windows: 创建并激活虚拟环境
py -m venv venv
venv\Scripts\activate
```

```bash
# 4. 安装运行依赖
pip install -r requirements.txt
```

```bash
# 5. macOS / Linux: 安装开发依赖和 pre-commit hooks
pip install -r requirements-dev.txt
python3 -m pre_commit install

# 6. macOS / Linux: 验证安装
python3 -m pre_commit run --all-files
python3 -m pytest tests/test_sync_flow.py tests/test_cleanup_flow.py -v
python3 -m pytest tests/ -v
```

```powershell
# 5. Windows: 安装开发依赖和 pre-commit hooks
pip install -r requirements-dev.txt
py -m pre_commit install

# 6. Windows: 验证安装
py -m pre_commit run --all-files
py -m pytest tests/test_sync_flow.py tests/test_cleanup_flow.py -v
py -m pytest tests/ -v
```

### 配置测试环境（可选）

如需测试同步功能：

```bash
# 使用交互式向导
python main.py init

# 或手动创建配置
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入测试账号信息
```

**获取配置信息：**
- `instance_url`：Mastodon 实例地址，如 `https://mastodon.social`
- `access_token`：**首选项** → **开发** → **新建应用**，只勾选 `read:statuses`
- `user_id`：访问 `https://<实例>/api/v1/accounts/lookup?acct=<用户名>`，获取 JSON 中的 `id`

⚠️ 不要将测试 token 提交到仓库。

### 开发流程

```bash
# 1. 同步上游更新
git checkout main
git fetch upstream
git merge upstream/main

# 2. 创建功能分支
git checkout -b feature/功能名称
# 或 git checkout -b fix/问题描述

# 3. 编写代码
# 遵循现有代码风格，添加必要注释

# 4. 运行检查和测试
python3 -m pre_commit run --all-files
python3 -m pytest tests/test_sync_flow.py tests/test_cleanup_flow.py -v
python3 -m pytest tests/ -v

# 5. 提交更改
git add .
git commit -m 'feat: 简短描述'
# Pre-commit hooks 会自动运行

# 6. 推送分支
git push origin 分支名称

# 7. 创建 Pull Request
# 访问 GitHub 仓库页面，点击 "New Pull Request"
```

Windows 用户可将上面的 `python3 -m ...` 改为 `py -m ...`；如果你的环境没有 `py`，再改用 `python -m ...`。

### 关于 `sync_state.json`

- `sync_state.json` 是仓库内受版本控制的同步状态文件，GitHub Actions 依赖它实现真正的增量同步
- 本地调试时如果你不想让它进入 `git status`，请使用本机私有规则 `.git/info/exclude`
- 不要把它重新加入项目级 `.gitignore`，否则自动化会退化成反复从头抓取历史数据

GitHub 已自动识别以下协作模板：
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

**提交类型：**
- `feat`: 新增功能
- `fix`: 修复问题
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建或工具配置

### 代码规范

项目使用以下工具保证代码质量：
- **black** - 代码格式化
- **isort** - import 排序
- **flake8** - 代码质量检查（行长度 150）
- **pre-commit** - 提交前自动检查
- **pytest smoke tests** - 流程级同步与 cleanup 校验

提交时会自动运行检查，如有问题会自动修复或提示。

### Pull Request 检查清单

- [ ] 代码通过所有 pre-commit 检查
- [ ] 所有测试通过
- [ ] 添加了必要的测试（如适用）
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有合并冲突

## 📚 文档贡献

文档改进同样重要：
- 修正拼写和语法错误
- 改进文档结构和可读性
- 添加使用示例
- 翻译成其他语言

## 🎓 行为准则

请保持友好、尊重的交流方式，共同营造良好的开源社区氛围。
