# Mastodon Vault Sync

一个自动化的 Mastodon 帖子同步工具，可以将您的帖子（包括媒体文件）完整地备份到 GitHub 仓库中，实现永久、安全的离线存档。

## ✨ 核心功能

*   **双重备份模式：**

    *   **汇总归档：** 所有帖子会被整理到一个位于仓库**根目录**的单一 Markdown 文件中（默认为 `archive.md`），方便您按时间线浏览。
    *   **独立文件：** 每一条帖子都会被保存为一个独立的 Markdown 文件，存放在指定文件夹中（默认为 `mastodon/`），便于独立引用和管理。
*   **全媒体备份：** 自动下载所有嘟文中的图片、视频等媒体文件到指定文件夹（默认为 `media/`），并在所有备份文件中使用本地相对路径链接，**实现真正的离线浏览**。即使 Mastodon 服务器无法访问，您仍然可以查看完整的帖子内容。
*   **自动化与智能化：**

    *   **定时执行：** 基于 GitHub Actions，可实现无人值守的定时同步（例如每 3 小时一次）。
    *   **智能同步：** 自动检测备份状态。首次运行执行**全量备份**；后续运行只同步新帖子的**增量备份**，高效节能。
    *   **安全可靠：** 通过 GitHub Secrets 管理您的个人凭证，确保 API 令牌等敏感信息不被泄露。
*   **高度可定制：** 您可以自由定义所有备份文件夹和文件的名称，满足个性化需求。

## 📁 项目结构

```
mastodon-sync/
├── main.py                 # 主程序脚本：负责执行 Mastodon 帖子同步的核心逻辑
├── config.example.yaml     # 配置文件模板：用于配置 Mastodon API 凭证和备份选项
├── requirements.txt        # Python依赖：列出项目所需的所有 Python 包
├── README.md              # 项目说明文档：您正在阅读的文档
├── LICENSE                 # MIT许可证：本项目使用的开源许可证
├── .github/
│   └── workflows/
│       └── sync.yml        # GitHub Actions 工作流：定义自动化同步任务的执行流程
├── mastodon/               # 单条帖子备份目录：存放每条帖子的独立 Markdown 文件
│   └── ...
├── media/                  # 媒体文件备份目录：存放帖子中引用的图片、视频等媒体文件
│   └── ...
├── archive.md              # 汇总归档文件：包含所有帖子的时间线式 Markdown 文件
└── sync_state.json        # 同步状态记录：记录上次同步的状态，用于增量备份
```

## 🔑 获取 Mastodon API 凭证

在使用本工具之前，您需要获取三项关键信息：**实例地址**、**用户 ID** 和 **访问令牌**。

### 实例地址

您的 Mastodon 实例 URL，例如 `https://mastodon.social`。

### 访问令牌

1.  登录 Mastodon → **首选项** → **开发** → **新建应用**
2.  **应用名称：** 随意填写 (例如 `Mastodon Sync Action`)
3.  **重定向 URI：** 填写 `urn:ietf:wg:oauth:2.0:oob`
4.  **权限范围 (Scopes)：** 仅需勾选 `read:statuses` 权限
5.  提交后，复制生成的 **"你的访问令牌"**

### 用户 ID

1.  访问 `https://<你的实例地址>/api/v1/accounts/lookup?acct=<你的用户名>`
2.  在返回的 JSON 数据中，找到 `"id":` 字段
3.  复制引号中的那串**纯数字**

## 🚀 快速开始

### 方式一：GitHub Actions (推荐)

此方式可以实现全自动、云端定时备份，是 "一次配置，永久运行" 的最佳选择。

#### 第 1 步：Fork 本仓库

点击本页面右上角的 **"Fork"** 按钮，将这个仓库复制到您自己的 GitHub 账号下。**后续所有操作均在您 Fork 后的仓库中进行。**

#### 第 2 步：配置 GitHub Secrets

这是保障您账户安全的关键步骤。您需要将 Mastodon API 凭证保存为 GitHub Secrets，以便 Actions 能够安全地访问您的 Mastodon 账户。

1.  在您 Fork 的仓库页面，点击 **"Settings"** → **"Secrets and variables"** → **"Actions"**。
2.  点击 **"New repository secret"** 按钮，依次创建下表中的 Secret：

| Secret 名称             | 示例值                              | 描述                                                                                                                                                                                                                                                            |
| ----------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MASTODON_INSTANCE_URL` | `https://mastodon.social`           | **【必需】** 您的 Mastodon 实例地址。                                                                                                                                                                                                                          |
| `MASTODON_USER_ID`      | `123456789012345678`                | **【必需】** 您的用户 ID。                                                                                                                                                                                                                                    |
| `MASTODON_ACCESS_TOKEN` | `Abc123xyz...`                      | **【必需】** 您的访问令牌。                                                                                                                                                                                                                                  |
| `ARCHIVE_FILENAME`      | `archive.md`                        | **【可选】** 根目录下汇总文件的名称。**默认值：** `archive.md`                                                                                                                                                                                                     |
| `POSTS_FOLDER`          | `mastodon`                          | **【可选】** 存放单条嘟文的文件夹名。**默认值：** `mastodon`                                                                                                                                                                                                       |
| `MEDIA_FOLDER`          | `media`                             | **【可选】** 存放媒体文件的文件夹名。**默认值：** `media`                                                                                                                                                                                                         |

#### 第 3 步：启用并运行 Action

1.  在您的仓库页面，点击顶部的 **"Actions"** 标签页。
2.  如果看到提示，请点击 **"I understand my workflows, go ahead and enable them"** 按钮。
3.  在左侧列表中，点击 **"Mastodon Vault Sync"** 工作流。
4.  点击右侧的 **"Run workflow"** 下拉菜单，然后再次点击绿色的 **"Run workflow"** 按钮，即可手动触发一次初始备份。

    *   **分支：** 保持默认的 `main` 分支。
    *   **强制全量同步：** 在某些情况下，您可能需要重新生成所有备份文件，只需勾选此选项。

任务将自动开始运行。首次运行会进行全量备份，之后会按预设时间自动进行增量同步。您可以在 Actions 页面查看任务的运行日志。

### 方式二：本地运行

此方式适合希望在自己电脑上手动执行，或与本地其他工具链（如 Obsidian）结合的用户。

#### 第 1 步：准备环境

1.  **克隆仓库：** 使用 `git clone https://github.com/Eyozy/mastodon-sync.git` 克隆项目到本地
2.  **安装 Python：** 确保您的系统安装了 Python 3.7 或更高版本
3.  **安装依赖：** 在项目目录中执行 `pip install -r requirements.txt`

#### 第 2 步：创建并配置 `config.yaml`

1.  复制配置模板：`cp config.example.yaml config.yaml`
2.  编辑配置文件：打开 `config.yaml` 并填入您的 Mastodon 凭证
3.  根据需要自定义备份路径和文件名

#### 第 3 步：运行脚本

```bash
# 执行智能同步 (推荐)
python main.py

# 强制执行全量同步
python main.py --full-sync
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1.  Fork 本仓库
2.  创建特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
