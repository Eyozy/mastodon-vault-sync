# Mastodon Vault Sync

一个自动化的 Mastodon 帖子同步工具，可以将您的帖子（包括媒体文件）完整地备份到 GitHub 仓库中，实现永久、安全的离线存档。

## ✨ 核心功能

* **双重备份模式：**
    * **汇总归档：** 所有帖子会被整理到一个位于仓库根目录的单一 Markdown 文件中（默认为 `archive.md`），方便您按时间线浏览。
    * **独立文件：** 每一条帖子都会被保存为一个独立的 Markdown 文件，存放在指定文件夹中（默认为 `mastodon/`），便于独立引用和管理。
* **全媒体备份：** 自动下载所有嘟文中的图片、视频等媒体文件到指定文件夹（默认为 `media/`），并在所有备份文件中使用本地相对路径链接，实现真正的离线浏览。
* **活动总结报告：** 自动生成包含年度热力图的活动总结文件（默认为 `README.md`），直观展示您的发帖活跃度。
* **自动化与智能化：**
    * **定时执行：** 基于 GitHub Actions，可实现无人值守的定时同步（例如每 3 小时一次）。
    * **智能同步：** 自动检测备份状态。首次运行执行全量备份；后续运行只同步新帖子和已编辑的帖子，高效节能。
    * **安全可靠：** 通过 GitHub Secrets 管理您的个人凭证，确保 API 令牌等敏感信息不被泄露。
* **高度可定制：** 您可以自由定义所有备份文件夹和文件的名称，满足个性化需求。
* **双重部署模式：**
    * **当前仓库：** 备份文件直接提交到当前仓库
    * **远程仓库：** 备份文件同步到独立的远程数据仓库（可选）

## 📁 项目结构
```
mastodon-sync/
├── .github/
│   └── workflows/
│       ├── sync.yml          # 主要的自动化同步工作流
│       └── cleanup.yml       # (可选) 手动清理工作流
├── mastodon/                 # (生成) 存放单条帖子的备份目录
│   └── ...
├── media/                    # (生成) 存放媒体文件的备份目录
│   └── ...
├── .gitignore                # Git 忽略文件配置
├── main.py                   # 主程序脚本
├── config.example.yaml       # 本地运行的配置文件模板
├── requirements.txt          # Python 依赖列表
├── README.md                 # 项目说明文档
├── archive.md                # (生成) 汇总归档文件
├── README.md                 # (生成) 活动总结报告
└── sync_state.json           # (生成) 同步状态记录
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

| Secret 名称             | 示例值                              | 描述                                     |
| ----------------------- | ----------------------------------- | ---------------------------------------- |
| `MASTODON_INSTANCE_URL` | `https://mastodon.social`           | **【必需】** 您的 Mastodon 实例地址。       |
| `MASTODON_USER_ID`      | `123456789012345678`                | **【必需】** 您的用户 ID。          |
| `MASTODON_ACCESS_TOKEN` | `Abc123xyz...`                      | **【必需】** 您的访问令牌。         |
| `ARCHIVE_FILENAME`      | `archive.md`                        | **【可选】** 根目录下汇总文件的名称。**默认值：** `archive.md` |
| `POSTS_FOLDER`          | `mastodon`                          | **【可选】** 存放单条嘟文的文件夹名。**默认值：** `mastodon` |
| `MEDIA_FOLDER`          | `media`                             | **【可选】** 存放媒体文件的文件夹名。**默认值：** `media` |
| `CHECK_EDIT_LIMIT`      | `40`                                | **【可选】** 增量同步时检查最近帖子的数量，默认为 `40`。 |

#### 第 3 步：配置远程仓库（可选）

如果您希望将备份同步到独立的远程仓库，请按以下步骤操作：

##### 3.1 创建新的远程仓库

1. 登录您的 GitHub 账号
2. 点击右上角的 **"+"** 按钮，选择 **"New repository"**
3. 填写仓库信息：
   - **Repository name:** 建议使用 `mastodon-backup` 或您喜欢的名称
   - **Description:** 可选，例如 "Mastodon 帖子自动备份"
   - **Public/Private:** 根据您的需求选择
4. 点击 **"Create repository"** 按钮

##### 3.2 生成 Personal Access Token (PAT)

1. 在 GitHub 页面右上角点击您的头像，选择 **"Settings"**
2. 在左侧菜单中找到并点击 **"Developer settings"**
3. 点击 **"Personal access tokens"** → **"Tokens (classic)"**
4. 点击 **"Generate new token"** → **"Generate new token (classic)"**
5. 配置 token 权限：
   - **Note:** 填写描述，例如 "Mastodon Backup Sync"
   - **Expiration:** 选择合适的过期时间
   - **Scopes:** 勾选以下权限：
     - ✅ **`repo`** - 完整的仓库访问权限
     - ✅ **`workflow`** - 工作流权限（可选）
6. 滚动到页面底部，点击 **"Generate token"** 按钮
7. **⚠️ 重要：** 请立即复制生成的 token（格式如 `ghp_xxx...`），因为页面刷新后您将无法再次看到它！

##### 3.3 配置 GitHub Secrets

在您 Fork 的仓库页面，点击 **"Settings"** → **"Secrets and variables"** → **"Actions"**。

点击 **"New repository secret"** 按钮，依次创建下表中的 Secret：

| Secret 名称             | 示例值                              | 描述                                     |
| ----------------------- | ----------------------------------- | ---------------------------------------- |
| `MASTODON_INSTANCE_URL` | `https://mastodon.social`           | **【必需】** 您的 Mastodon 实例地址。       |
| `MASTODON_USER_ID`      | `123456789012345678`                | **【必需】** 您的用户 ID。          |
| `MASTODON_ACCESS_TOKEN` | `Abc123xyz...`                      | **【必需】** 您的访问令牌。         |
| `ARCHIVE_FILENAME`      | `archive.md`                        | **【可选】** 根目录下汇总文件的名称。**默认值：** `archive.md` |
| `POSTS_FOLDER`          | `mastodon`                          | **【可选】** 存放单条嘟文的文件夹名。**默认值：** `mastodon` |
| `MEDIA_FOLDER`          | `media`                             | **【可选】** 存放媒体文件的文件夹名。**默认值：** `media` |
| `CHECK_EDIT_LIMIT`      | `40`                                | **【可选】** 增量同步时检查最近帖子的数量，默认为 `40`。 |
| `ENABLE_PUSH_TO_DATA_REPO` | `true`                              | **【可选】** 启用远程仓库同步，**默认值：** `false` |
| `TARGET_REPO_USERNAME`  | `your-username`                     | **【可选】** 目标仓库的用户名 |
| `TARGET_REPO_NAME`      | `your-backup-repo`                  | **【可选】** 目标仓库名称 |
| `TARGET_REPO_PAT`       | `ghp_xxx...`                        | **【可选】** 目标仓库的 Personal Access Token |

#### 第 4 步：启用并运行 Action

1.  在您的仓库页面，点击顶部的 **"Actions"** 标签页。
2.  如果看到提示，请点击 **"I understand my workflows, go ahead and enable them"** 按钮。
3.  在左侧列表中，点击 **"Mastodon Sync"** 工作流。
4.  点击右侧的 **"Run workflow"** 下拉菜单，然后再次点击绿色的 **"Run workflow"** 按钮，即可手动触发一次初始备份。
    * **分支：** 保持默认的 `main` 分支。
    * **强制全量同步：** 在某些情况下（如更新脚本后想刷新格式），您可能需要重新生成所有备份文件，只需勾选此选项。

任务将自动开始运行。首次运行会进行全量备份，之后会按预设时间自动进行增量同步。您可以在 Actions 页面查看任务的运行日志。

### 方式二：本地运行

此方式适合希望在自己电脑上手动执行，或与本地其他工具链结合的用户。

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

### 🗑️ 清理已删除的帖子

如果您在 Mastodon 上删除了某些帖子，并希望在您的备份中也移除它们，可以运行清理模式。

注意：这是一个破坏性操作，会永久删除您的本地备份文件。请谨慎使用。

**本地清理**

在终端中运行：

```Bash
python main.py --cleanup
```

此命令会获取您服务器上的所有帖子列表，并与本地 `mastodon/` 文件夹下的文件进行比对，删除所有在服务器上已不存在的单条帖子备份。

**GitHub Actions 清理**

在您的仓库页面，点击顶部的 **"Actions"** 标签页。

在左侧列表中，找到并点击 **"Manual Cleanup"** 工作流。

点击右侧的 **"Run workflow"** 下拉菜单，然后再次点击绿色的 **"Run workflow"** 按钮。

重要提示：清理模式不会自动更新您的汇总文件 (`archive.md`)。在执行清理后，您需要运行一次强制全量同步来重新生成一个干净的汇总文件。

## 📊 活动总结报告

工具会自动生成一份活动总结报告，包含以下内容：

### 年度发帖统计
- 显示当前年度的发帖总数
- 直观的发帖活跃度概览

### 热力图可视化
- 基于 GitHub 贡献图风格的热力图
- 按日期显示发帖频率
- 不同颜色代表不同的发帖数量
- 鼠标悬停可查看具体日期的发帖数量

### 报告位置
- 默认生成在仓库根目录的 `README.md` 文件中
- 包含截至当前日期的活动概览
- 提供热力图的 Markdown 嵌入显示

## 🔄 同步模式说明

### 全量同步模式
**触发条件：**
- 首次运行
- 手动勾选"强制全量同步"
- 同步状态文件损坏

**执行操作：**
- 清理所有旧的备份文件
- 重新下载所有帖子
- 重新生成所有备份文件
- 重新生成活动总结报告

### 增量同步模式
**触发条件：**
- 非首次运行
- 未勾选"强制全量同步"
- 同步状态文件正常

**执行操作：**
- 只下载新的帖子
- 只更新已编辑的帖子
- 保持现有备份文件不变
- 更新活动总结报告（如有新内容）



## 🤝 贡献指南

欢迎为 Mastodon Vault Sync 项目贡献您的力量！无论是报告问题、提出建议还是提交代码，您的贡献都非常宝贵。

### 🐛 报告问题

如果您在使用过程中遇到任何问题，请通过以下方式报告：

1.  访问项目的 [Issues 页面](https://github.com/Eyozy/mastodon-vault-sync/issues)
2.  点击 "New Issue" 按钮
3.  详细描述您遇到的问题，包括：
    - 问题的具体表现
    - 重现步骤
    - 期望的行为
    - 实际发生的行为
    - 相关的环境信息（操作系统、Python 版本等）

### 💡 功能建议

如果您有新的功能想法或改进建议，欢迎：

1.  在 Issues 页面创建新的功能请求
2.  详细描述您的建议
3.  解释为什么这个功能对项目有价值
4.  如果可能，提供实现方案或伪代码

### 🛠️ 代码贡献

#### 开发环境设置

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

#### 开发流程

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

#### 代码规范

- 遵循 PEP 8 Python 编码规范
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串
- 保持代码简洁和可读性

#### 测试要求

- 新功能应包含相应的测试
- 确保所有测试通过
- 测试覆盖率应保持在合理水平

### 📚 文档贡献

文档改进同样重要！您可以：

- 修正拼写错误和语法问题
- 改进文档结构和可读性
- 添加使用示例
- 翻译文档到其他语言

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
