# Mastodon Vault Sync

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Enabled-green.svg)](https://github.com/Eyozy/mastodon-sync/actions)

一个自动化的 Mastodon 帖子同步工具，可以将您的帖子（包括媒体文件）完整地备份到 GitHub 仓库中，实现永久、安全的离线存档。

## ✨ 核心功能

- **双重备份模式**:
  - **汇总归档**: 所有帖子会被整理到一个位于仓库**根目录**的单一 Markdown 文件中（默认为 `archive.md`），方便您按时间线浏览。
  - **独立文件**: 每一条帖子都会被保存为一个独立的 Markdown 文件，存放在指定文件夹中（默认为 `mastodon/`），便于独立引用和管理。
- **全媒体备份**: 自动下载所有嘟文中的图片、视频等媒体文件到指定文件夹（默认为 `media/`），并在所有备份文件中使用本地相对路径链接，实现真正的离线可用。
- **自动化与智能化**:
  - **定时执行**: 基于 GitHub Actions，可实现无人值守的定时同步（例如每 3 小时一次）。
  - **智能同步**: 自动检测备份状态。首次运行执行**全量备份**；后续运行只同步新帖子的**增量备份**，高效节能。
  - **安全可靠**: 通过 GitHub Secrets 管理您的个人凭证，确保 API 令牌等敏感信息不被泄露。
- **高度可定制**: 您可以自由定义所有备份文件夹和文件的名称，满足个性化需求。

## 🚀 快速开始

### 方式一：GitHub Actions (推荐)

此方式可以实现全自动、云端定时备份，是"一次配置，永久运行"的最佳选择。

#### 第 1 步：Fork 本仓库

点击本页面右上角的 **"Fork"** 按钮，将这个仓库复制到您自己的 GitHub 账号下。后续所有操作均在您 Fork 后的仓库中进行。

#### 第 2 步：获取 Mastodon API 凭证

您需要准备三项信息：**实例地址**、**用户 ID** 和 **访问令牌**。

1.  **实例地址**: 您的 Mastodon 网址，例如 `https://mastodon.social`。
2.  **访问令牌**:
    - 登录 Mastodon → **首选项** → **开发** → **新建应用**。
    - **应用名称**: 随意填写 (例如 `Mastodon Sync Action`)。
    - **重定向 URI**: 填写 `urn:ietf:wg:oauth:2.0:oob`。
    - **权限范围 (Scopes)**: 仅需勾选 `read:statuses` 权限。
    - 提交后，复制生成的 **"你的访问令牌"**。
3.  **用户 ID**:
    - 访问 `https://<你的实例地址>/api/v1/accounts/lookup?acct=<你的用户名>`。
    - 在返回的 JSON 数据中，找到 `"id":` 字段，复制引号中的那串**纯数字**。

#### 第 3 步：配置 GitHub Secrets

这是保障您账户安全的关键步骤。

1.  在您 Fork 的仓库页面，点击 **"Settings"** → **"Secrets and variables"** → **"Actions"**。
2.  点击 **"New repository secret"** 按钮，依次创建下表中的 Secret：

| Secret 名称             | 示例值                              | 描述                                     |
| ----------------------- | ----------------------------------- | ---------------------------------------- |
| `MASTODON_INSTANCE_URL` | `https://mastodon.social`           | **【必需】** 您的 Mastodon 实例地址。       |
| `MASTODON_USER_ID`      | `123456789012345678`                | **【必需】** 您的用户 ID。          |
| `MASTODON_ACCESS_TOKEN` | `Abc123xyz...`                      | **【必需】** 您的访问令牌。         |
| `ARCHIVE_FILENAME`      | `archive.md`                        | **【可选】** 根目录下汇总文件的名称。 |
| `POSTS_FOLDER`          | `mastodon`                          | **【可选】** 存放单条嘟文的文件夹名。 |
| `MEDIA_FOLDER`          | `media`                             | **【可选】** 存放媒体文件的文件夹名。 |
| `TARGET_REPO`           | `username/repository`              | **【可选】** 推送到的外部仓库。       |
| `PAT`                   | `ghp_xxxxxxxxxxxxxxxxxxxx`          | **【可选】** 个人访问令牌（当使用 TARGET_REPO 时需要）。 |

#### 第 4 步：启用并运行 Action

1.  在您的仓库页面，点击顶部的 **"Actions"** 标签页。
2.  如果看到提示，请点击 **"I understand my workflows, go ahead and enable them"** 按钮。
3.  在左侧列表中，点击 **"Mastodon Sync"** 工作流。
4.  点击右侧的 **"Run workflow"** 下拉菜单，然后再次点击绿色的 **"Run workflow"** 按钮，即可手动触发一次初始备份。

任务将自动开始运行。首次运行会进行全量备份，之后会按预设时间自动进行增量同步。

---

### 方式二：本地运行

此方式适合希望在自己电脑上手动执行，或与本地其他工具链结合的用户。

#### 第 1 步：准备环境

1.  **下载代码**: 将本项目所有文件下载到您电脑的某个文件夹中。
2.  **安装 Python**: 确保您的电脑上安装了 Python 3.7 或更高版本。
3.  **安装依赖**: 在项目文件夹中打开终端，运行 `pip install -r requirements.txt`。

#### 第 2 步：创建并配置 `config.yaml`

1.  将项目中的 `config.example.yaml` 文件复制一份，并重命名为 `config.yaml`。
2.  打开 `config.yaml` 文件，填写您的 Mastodon 凭证（获取方法同上）。
3.  在 `backup` 部分，您可以自定义所有备份文件和文件夹的名称与路径。

#### 第 3 步：运行脚本

在项目文件夹中打开终端，运行以下命令：

```bash
# 执行智能同步 (推荐)
python main.py

# 如果需要，可以强制执行全量同步
python main.py --full-sync
```

**运行日志示例 (本地)**

当您成功在本地运行脚本后，终端会显示类似以下的日志信息：
```bash
C:\Users\Mastodon-Sync>python main.py
2025-08-16 19:23:39,442 - INFO - ========================================
2025-08-16 19:23:39,443 - INFO -  Mastodon Sync 开始运行
2025-08-16 19:23:39,443 - INFO - ========================================
2025-08-16 19:23:39,443 - WARNING - ⚠️ 未找到完整的环境变量配置，将尝试从 config.yaml 文件加载。
2025-08-16 19:23:39,453 - INFO - ✔ 配置文件加载成功。
2025-08-16 19:23:39,454 - WARNING - ⚠️  检测到 'archive.md' 文件不存在，将自动执行全量同步。
2025-08-16 19:23:39,455 - INFO - ℹ️  已删除旧的同步状态文件。
2025-08-16 19:23:39,455 - INFO - 🚀 开始从 https://mastodon.social 获取帖子...
2025-08-16 19:23:39,455 - INFO - 📄 正在获取第 1 页...
2025-08-16 19:23:40,314 - INFO - ✔ 成功获取 7 条帖子。
2025-08-16 19:23:40,326 - INFO - ✍️  已更新归档文件：C:\Users\Mastodon-Sync\archive.md
2025-08-16 19:23:40,328 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-12_170625.md
2025-08-16 19:23:40,329 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-12_174009.md
2025-08-16 19:23:40,335 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-14_003452.md
2025-08-16 19:23:40,337 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-14_200142.md
2025-08-16 19:23:40,338 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-15_165818.md
2025-08-16 19:23:40,339 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-15_180059.md
2025-08-16 19:23:40,341 - INFO - 📄 已备份单条嘟文：C:\Users\Mastodon-Sync\mastodon\2025-08-16_035048.md
...
2025-08-16 19:23:40,342 - INFO - ✔ 同步状态已保存。
2025-08-16 19:23:40,342 - INFO - ========================================
2025-08-16 19:23:40,342 - INFO -  ✅ 同步完成！
2025-08-16 19:23:40,342 - INFO - ========================================
```

## 📁 项目结构

```
mastodon-sync/
├── main.py                 # 主程序脚本
├── config.example.yaml     # 配置文件模板
├── requirements.txt        # Python依赖
├── README.md              # 项目说明文档
├── LICENSE                 # MIT许可证
├── .github/
│   └── workflows/
│       └── sync.yml        # GitHub Actions工作流
├── mastodon/               # 单条帖子备份目录
│   ├── 2025-08-12_170625_115014997459049267.md
│   └── ...
├── media/                  # 媒体文件备份目录
│   ├── 115042939752568383-5e30d8fe4fd16609.jpg
│   └── ...
├── archive.md              # 汇总归档文件
├── sync_state.json        # 同步状态记录
└── target_repo/           # 目标仓库（可选）
    ├── mastodon/
    ├── media/
    ├── archive.md
    └── sync_state.json
```

## ⚙️ 配置说明

### 环境变量配置 (GitHub Actions)

| 变量名 | 必需 | 默认值 | 描述 |
|--------|------|--------|------|
| `MASTODON_INSTANCE_URL` | 是 | - | Mastodon 实例地址 |
| `MASTODON_USER_ID` | 是 | - | 用户 ID |
| `MASTODON_ACCESS_TOKEN` | 是 | - | API 访问令牌 |
| `ARCHIVE_FILENAME` | 否 | `archive.md` | 汇总文件名 |
| `POSTS_FOLDER` | 否 | `mastodon` | 帖子文件夹名 |
| `MEDIA_FOLDER` | 否 | `media` | 媒体文件夹名 |
| `TARGET_REPO` | 否 | - | 目标仓库（格式：username/repo） |
| `PAT` | 否 | - | 个人访问令牌（TARGET_REPO 需要） |
| `FORCE_FULL_SYNC` | 否 | `false` | 强制全量同步 |

### 配置文件格式 (本地运行)

```yaml
mastodon:
  instance_url: "https://mastodon.social"
  user_id: "YOUR_USER_ID"
  access_token: "YOUR_ACCESS_TOKEN"

backup:
  path: "."
  posts_folder: "mastodon"
  filename: "archive.md"
  media_folder: "media"

sync:
  state_file: "sync_state.json"
```

## 🔧 高级功能

### 外部仓库同步

如果您希望将同步的帖子推送到另一个仓库，可以：

1. 在 GitHub Secrets 中设置 `TARGET_REPO` 为目标仓库地址（格式：`username/repository`）
2. 设置 `PAT` 为具有写入权限的个人访问令牌
3. 系统会自动将同步的文件推送到指定仓库

### 强制全量同步

在某些情况下，您可能需要重新生成所有备份文件：

- **GitHub Actions**: 在运行工作流时勾选 "Force full sync" 选项
- **本地运行**: 使用 `python main.py --full-sync` 命令

## 📊 输出格式

### 汇总归档格式 (`archive.md`)

```markdown
# 2025-08-22
## 21:59 📝 嘟文

**内容**：改了下博客的样式，新界面（图二）看着更舒服些
![Image](media/115072760752126573-443789f4c56b1013.png)
![Image](media/115072761389814928-28b837b5dd43cfc2.png)

**原始嘟文**：https://mastodon.social/@Eyoz/115072772649804673

---
```

### 独立文件格式 (`mastodon/2025-08-22_215924_115072772649804673.md`)

```markdown
---
createdAt: '2025-08-22 21:59:24'
id: '115072772649804673'
source: https://mastodon.social/@Eyoz/115072772649804673
tags: ['#blog', '#webdev']
type: toot
---

改了下博客的样式，新界面（图二）看着更舒服些
```

## 🐛 故障排除

### 常见问题

1. **认证失败**
   - 检查 API 令牌是否具有 `read:statuses` 权限
   - 确认用户 ID 是否正确（必须是纯数字）

2. **网络连接问题**
   - 确保可以访问 Mastodon API
   - 检查防火墙设置

3. **权限问题**
   - 确保 GitHub Actions 有写入权限
   - 检查 PAT 是否具有仓库写入权限

### 日志分析

程序会输出详细的日志信息，包括：
- 配置加载状态
- API 请求状态
- 文件下载进度
- 同步结果统计

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Mastodon API](https://docs.joinmastodon.org/api/) - 提供数据接口
- [GitHub Actions](https://docs.github.com/en/actions) - 提供自动化平台
- [Python](https://www.python.org/) - 编程语言

## 📞 联系方式

- 项目地址：[https://github.com/Eyozy/mastodon-sync](https://github.com/Eyozy/mastodon-sync)
- 作者：[Eyozy](https://github.com/Eyozy)
