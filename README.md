# Mastodon Vault Sync

一个自动化的 Mastodon 帖子同步工具，将你的所有帖子（含媒体文件）完整备份到本地或 GitHub 仓库，实现永久、安全的离线存档。

## ✨ 核心特性

### 📦 双重备份机制
- **汇总归档**：所有帖子整理为单一大文件（默认 `archive.md`），按时间线完整呈现
- **独立文件**：每帖存为单独 Markdown 文件（默认 `mastodon/` 目录），便于索引与引用
- **媒体本地化**：自动下载所有图片/视频到 `media/` 目录，所有备份文件使用本地相对路径

### 🤖 智能自动化
- **定时同步**：基于 GitHub Actions 实现无人值守的自动备份
- **增量更新**：自动检测备份状态，首次全量备份，后续仅同步新增或修改的内容
- **性能优化**：仅在有新内容时更新统计信息，避免不必要的重复计算
- **错误容忍**：优雅处理文件锁定和访问权限问题

### 🔧 高度可定制
- 自由定义备份文件夹名称
- 支持双重部署模式：当前仓库备份或独立远程仓库备份
- 提供中国时区（GMT+8）支持

### 🔒 安全可靠
- 通过 GitHub Secrets 管理 API 令牌等敏感信息
- 采用 MIT 许可证，完全开源透明

## 📁 项目结构

```
mastodon-vault-sync/
├── .github/workflows/
│   ├── ci.yml                 # 代码检查与测试工作流
│   ├── sync.yml               # 主同步工作流
│   └── cleanup.yml            # 手动清理工作流
├── .github/ISSUE_TEMPLATE/    # Issue 模板
├── .github/pull_request_template.md
├── src/                       # 源代码目录
│   ├── __init__.py            # 版本信息
│   ├── api.py                 # Mastodon API 调用
│   ├── backup.py              # 备份逻辑
│   ├── cli.py                 # 命令行接口
│   ├── config.py              # 配置管理
│   ├── render.py              # HTML/Markdown 渲染
│   ├── utils.py               # 工具函数
│   └── assets/                # 静态资源（CSS/JS）
├── tests/                     # 测试文件
│   ├── test_api.py
│   ├── test_backup.py
│   ├── test_render.py
│   └── test_utils.py
├── main.py                    # 主程序入口
├── config.example.yaml        # 配置模板
├── requirements.txt           # 运行时依赖
├── requirements-dev.txt       # 开发与测试依赖
├── .pre-commit-config.yaml    # 代码检查配置
├── .flake8                    # Flake8 配置
├── archive.md                 # (生成) 汇总归档文件
├── sync_state.json            # (生成) 同步状态
├── mastodon/                  # (生成) 单帖备份目录
├── media/                     # (生成) 媒体文件目录
└── index.html                 # (生成) 可浏览的网页界面
```

## 🔑 获取 Mastodon API 凭证

### 1. 实例地址
实例地址就是你登录 Mastodon 时浏览器地址栏里的域名。

常见例子：

- 如果你平时登录的是 `https://mastodon.social/@yourname`，那实例地址就是 `https://mastodon.social`
- 如果你平时登录的是 `https://m.cmx.im/@yourname`，那实例地址就是 `https://m.cmx.im`

填写时只保留协议和域名，不要带 `@用户名`、帖子路径、参数或最后的 `/`。

### 2. 访问令牌
1. 登录你的 Mastodon 账号
2. 点击右侧或左下角的 **首选项 / Preferences / Settings**
3. 进入 **开发 / Development** 页面
4. 点击 **新建应用 / New application**
5. 按下表填写：

| 字段 | 填写内容 |
|------|----------|
| 应用名称 | `Mastodon Vault Sync` 或任意你能识别的名称 |
| 网站 | 可留空 |
| Redirect URI / 重定向 URI | `urn:ietf:wg:oauth:2.0:oob` |
| Scopes / 权限范围 | 只保留 `read:statuses` |

6. 提交创建应用
7. 打开刚创建的应用详情页
8. 找到 **Your access token / 访问令牌**
9. 复制完整 token，保存到安全位置

如果页面里没有直接显示 token，可在应用详情页重新生成。⚠️ 不要将 token 贴进公开仓库或截图分享。

### 3. 用户 ID
用户 ID 不是用户名，也不是 `@name@instance`，而是一串纯数字。

获取方法：

1. 确认你的用户名
2. 在浏览器中访问：

```text
https://<你的实例地址>/api/v1/accounts/lookup?acct=<你的用户名>
```

3. 例如：

```text
https://mastodon.social/api/v1/accounts/lookup?acct=YourUsername
```

4. 页面会返回一段 JSON
5. 找到最前面的 `"id"` 字段，例如：

```json
{
  "id": "123456789012345678",
  "username": "YourUsername"
}
```

6. 复制 `"id"` 后面的纯数字，这就是 `MASTODON_USER_ID` 或 `mastodon.user_id` 要填的值

如果你的账号是跨实例形式（例如 `yourname@example.com`），将 `acct=` 后面的值改为完整账号标识再查询。

## 🚀 快速开始

### 方式一：本地使用（推荐）

#### 安装和配置

```bash
# 克隆仓库
git clone https://github.com/Eyozy/mastodon-vault-sync.git
cd mastodon-vault-sync
```

```bash
# macOS / Linux: 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

```powershell
# Windows: 创建并激活虚拟环境
py -m venv venv
venv\Scripts\activate
```

```bash
# 安装运行依赖
pip install -r requirements.txt

# 运行配置向导
python main.py init
```

**为什么使用虚拟环境？**
- 隔离项目依赖，避免与其他 Python 项目冲突
- 便于管理和清理依赖包

按提示输入以下信息：

1. **Mastodon 实例地址**
   例如：`https://mastodon.social`

2. **用户 ID**（纯数字）
   获取方法见下方说明

3. **访问令牌**（输入时不显示）
   从 Mastodon 应用设置中获取

4. **备份路径**
   默认：`backup` (在项目根目录下创建)

配置完成后会自动生成 `config.yaml` 文件。

#### 使用

**注意**：每次使用前需要先激活虚拟环境。

```bash
# macOS / Linux
source venv/bin/activate
```

```powershell
# Windows
venv\Scripts\activate
```

**常用命令**：

```bash
# 首次同步（获取所有历史帖子）
python main.py sync --full

# 日常增量同步（只获取新帖子）
python main.py sync

# 查看同步状态
python main.py status

# 检查配置是否正确
python main.py check

# 清理已删除的帖子
python main.py cleanup

# 显示版本号
python main.py version

# 显示帮助信息
python main.py help
```

**提示**：
- 在虚拟环境中，项目命令统一使用 `python main.py ...`
- 如果你的 Windows 环境没有 `py` 命令，可以把文档里的 `py -m ...` 改成 `python -m ...`
- 首次运行建议使用 `sync --full` 获取完整历史记录

### 方式二：GitHub Actions（自动化）

#### 第 1 步：Fork 仓库
点击页面右上角 **Fork** 按钮，将仓库复制到你的 GitHub 账号

#### 第 2 步：启用 Actions 写权限

1. 打开你 Fork 后的仓库
2. 进入 **Settings** → **Actions** → **General**
3. 确认 Actions 已启用
4. 在 **Workflow permissions** 中选择 **Read and write permissions**
5. 点击 **Save**

如果跳过此步骤，工作流最后的 `git push` 会因为缺少写权限而失败。

#### 第 3 步：配置 Secrets

1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 按下表逐个创建 Secret
4. 所有必需的 Secret 创建完成后，再到 **Actions** 页面运行工作流

在你的 Fork 仓库中依次添加以下 Secrets：

| Secret 名称             | 示例值                              | 必填 | 描述 |
|-------------------------|-----------------------------------|------|------|
| `MASTODON_INSTANCE_URL` | `https://mastodon.social`          | ✅   | Mastodon 实例地址 |
| `MASTODON_USER_ID`      | `123456789012345678`               | ✅   | 用户 ID |
| `MASTODON_ACCESS_TOKEN` | `Abc123xyz...`                     | ✅   | 访问令牌 |
| `ARCHIVE_FILENAME`      | `archive.md`                       | ❌   | 汇总文件名，默认 `archive.md` |
| `POSTS_FOLDER`          | `mastodon`                         | ❌   | 帖子目录名，默认 `mastodon` |
| `MEDIA_FOLDER`          | `media`                            | ❌   | 媒体目录名，默认 `media` |
| `CHINA_TIMEZONE`        | `false`                            | ❌   | 时区设置：`true` 使用中国时区 (GMT+8)，`false` 使用 UTC。默认 `false` |

`MASTODON_INSTANCE_URL`、`MASTODON_USER_ID`、`MASTODON_ACCESS_TOKEN` 这三个 Secret 必须配置，否则同步脚本无法启动。

建议按下面的映射填写：

| 你手里的值 | 对应的 Secret |
|-----------|---------------|
| `https://mastodon.social` 这种实例地址 | `MASTODON_INSTANCE_URL` |
| JSON 里的纯数字 `"id"` | `MASTODON_USER_ID` |
| Mastodon 应用详情页里的 access token | `MASTODON_ACCESS_TOKEN` |

当前仓库自带的 `sync.yml` 会在 GitHub Actions 中固定使用 `mastodon/` 和 `media/` 两个目录名，因此即使你填写了 `POSTS_FOLDER` 或 `MEDIA_FOLDER` Secret，工作流也不会改变目录名。本地运行时才会读取 `config.yaml` 里的自定义目录配置。

**配置远程仓库同步（可选）**：

#### 1. 创建新的远程仓库
1. 登录你的 GitHub 账号
2. 点击右上角的 **"+"** 按钮，选择 **"New repository"**
3. 填写仓库信息：
   - **Repository name:** 建议使用 `mastodon-backup` 或你喜欢的名称
   - **Description:** 可选，例如 "Mastodon 帖子自动备份"
   - **Public/Private:** 根据你的需求选择
4. 点击 **"Create repository"** 按钮

#### 2. 生成 Personal Access Token (PAT)
1. 在 GitHub 页面右上角点击你的头像，选择 **"Settings"**
2. 在左侧菜单中找到并点击 **"Developer settings"**
3. 点击 **"Personal access tokens"** → **"Tokens (classic)"**
4. 点击 **"Generate new token"** → **"Generate new token (classic)"**
5. 配置 token 权限：
   - **Note:** 填写描述，例如 "Mastodon Backup Sync"
   - **Expiration:** 选择合适的过期时间
   - **Scopes:** 勾选 **`repo`** 权限（完整的仓库访问权限）
6. 滚动到页面底部，点击 **"Generate token"** 按钮
7. **⚠️ 重要：** 请立即复制生成的 token（格式如 `ghp_xxx...`），页面刷新后将无法再次看到！

#### 3. 配置远程仓库 Secrets

| Secret 名称             | 示例值                              | 必填 | 描述 |
|-------------------------|-----------------------------------|------|------|
| `ENABLE_PUSH_TO_DATA_REPO` | `true`                          | ✅   | 启用远程同步 |
| `TARGET_REPO_USERNAME`  | `your-username`                    | ✅   | 目标仓库的用户名 |
| `TARGET_REPO_NAME`      | `mastodon-backup`                  | ✅   | 目标仓库名称 |
| `TARGET_REPO_PAT`       | `ghp_xxx...`                       | ✅   | 刚刚生成的 Personal Access Token |

只有在你明确想把备份推送到另一个仓库时，才需要配置这一组 Secret；否则保持不填，工作流会直接提交到当前 Fork 仓库。

#### 第 4 步：运行同步

1. 进入仓库 **Actions** 标签页，启用工作流
2. 点击 **Mastodon Vault Sync** 工作流
3. 点击 **Run workflow**
4. 首次运行建议勾选 `force_full_sync`
5. 等待任务完成后，检查仓库里是否出现 `archive.md`、`README.md`、`index.html`、`mastodon/`、`media/`
6. 首次运行完成后，系统将自动按定时规则执行增量同步

## 🗑️ 清理已删除的帖子

### GitHub Actions 清理
1. 进入 **Actions** 标签页
2. 点击 **Mastodon Vault Cleanup** → **Run workflow**
3. 这个工作流会执行一次全量重建：删除旧的 `archive.md`、`mastodon/`、`media/` 等备份产物后，重新从服务器拉取当前仍存在的帖子
4. 运行完成后，仓库中的汇总文件、单帖文件、媒体文件、HTML 页面和热力图会一起更新

### 本地清理
```bash
# 清理模式：执行全量重建，自动移除本地已不存在于服务器上的帖子和媒体
python main.py cleanup
```

**注意：**
- 清理操作会永久删除当前备份目录中的旧帖子和旧媒体文件
- `cleanup` 本身就会完成重建，不需要再额外执行 `sync --full`

## 👨‍💻 开发设置

### 环境设置

```bash
# 安装运行依赖
pip install -r requirements.txt
```

```bash
# macOS / Linux: 安装开发依赖、pre-commit hooks 并运行检查
pip install -r requirements-dev.txt
python3 -m pre_commit install
python3 -m pre_commit run --all-files
```

```powershell
# Windows: 安装开发依赖、pre-commit hooks 并运行检查
pip install -r requirements-dev.txt
py -m pre_commit install
py -m pre_commit run --all-files
```

### 代码规范

项目使用以下工具保证代码质量：
- **black** - 代码格式化
- **isort** - import 排序
- **flake8** - 代码质量检查
- **pre-commit** - 提交前自动检查

提交代码时会自动运行检查，如有问题会自动修复或提示。

### 运行测试

```bash
# macOS / Linux: 运行所有测试
python3 -m pytest tests/ -v

# macOS / Linux: 运行特定测试
python3 -m pytest tests/test_basic.py -v
```

```powershell
# Windows: 运行所有测试
py -m pytest tests/ -v

# Windows: 运行特定测试
py -m pytest tests/test_basic.py -v
```

更详细的测试说明和常见问题见 [tests/README.md](tests/README.md)。

### 贡献指南

欢迎提交 Issue 和 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
