# Mastodon Vault Sync

一个自动化的 Mastodon 帖子同步工具，将你的所有帖子（含媒体文件）完整备份到 GitHub 仓库，实现永久、安全的离线存档。

## ✨ 核心特性

### 📦 双重备份机制
- **汇总归档**：所有帖子整理为单一大文件（默认 `archive.md`），按时间线完整呈现
- **独立文件**：每帖存为单独 Markdown 文件（默认 `mastodon/` 目录），便于索引与引用
- **媒体本地化**：自动下载所有图片/视频到 `media/` 目录，所有备份文件使用本地相对路径

### 🤖 智能自动化
- **定时同步**：基于 GitHub Actions 实现无人值守的定时备份
- **增量更新**：自动检测备份状态，首次全量备份，后续仅同步新增/修改内容
- **性能优化**：仅在有新内容时更新统计信息，避免重复计算
- **错误容忍**：改进权限错误处理，优雅处理文件锁定和访问权限问题

### 🔧 高度可定制
- 自由定义备份文件夹名称
- 支持双重部署模式：当前仓库备份或独立远程仓库备份
- 提供中国时区（GMT+8）支持选项

### 🔒 安全可靠
- 通过 GitHub Secrets 管理 API 令牌等敏感信息
- 采用 MIT 许可证，完全开源透明

## 📁 项目结构

```
mastodon-vault-sync/
├── .github/workflows/
│   ├── sync.yml          # 主同步工作流
│   └── cleanup.yml       # 手动清理工作流（可选）
├── mastodon/             # (生成) 单条帖子备份目录
├── media/                # (生成) 媒体文件备份目录
├── .gitignore            # Git 忽略配置
├── main.py               # 主程序脚本
├── config.example.yaml   # 本地运行配置模板
├── requirements.txt      # Python 依赖
├── README.md             # 项目说明文档
├── archive.md            # (生成) 汇总归档文件
├── sync_state.json       # (生成) 同步状态记录
└── LICENSE               # 许可证文件
```

## 🔑 获取 Mastodon API 凭证

### 1. 实例地址
你的 Mastodon 服务器 URL，例如 `https://mastodon.social`

### 2. 访问令牌
1. 登录 Mastodon → **首选项** → **开发** → **新建应用**
2. 应用名称：任意（例如 `Mastodon Vault Sync`）
3. 重定向 URI：填写 `urn:ietf:wg:oauth:2.0:oob`
4. 权限范围：仅勾选 `read:statuses`
5. 提交后复制生成的访问令牌

### 3. 用户 ID
1. 访问 `https://<实例地址>/api/v1/accounts/lookup?acct=<用户名>`
2. 在返回的 JSON 中找到 `"id"` 字段的纯数字值

## 🚀 快速开始

### 方式一：GitHub Actions（推荐）

#### 第 1 步：Fork 仓库
点击页面右上角 **Fork** 按钮，将仓库复制到你的 GitHub 账号

#### 第 2 步：配置 Secrets

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

#### 第 3 步：运行同步

1. 进入仓库 **Actions** 标签页，启用工作流
2. 点击 **Mastodon Sync** → **Run workflow**，手动触发初始备份
3. 首次运行完成后，系统将自动按定时规则执行增量同步

### 方式二：本地运行

#### 第 1 步：安装环境

```bash
# 克隆仓库
git clone https://github.com/Eyozy/mastodon-vault-sync.git
cd mastodon-vault-sync

# 安装 Python 依赖
pip install -r requirements.txt
```

#### 第 2 步：配置文件

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件，填入你的凭证
```

**配置说明：**

在 `config.yaml` 中，你需要配置以下内容：

```yaml
mastodon:
  instance_url: "https://mastodon.social"  # 你的 Mastodon 实例地址
  user_id: "123456789012345678"             # 你的用户 ID
  access_token: "your_access_token"         # 你的访问令牌

backup:
  path: "."                                 # 本地备份路径
  posts_folder: "mastodon"                  # 帖子目录名
  filename: "archive.md"                    # 汇总文件名
  media_folder: "media"                     # 媒体目录名

sync:
  state_file: "sync_state.json"             # 同步状态文件名
  china_timezone: true                      # 时区设置（见下方说明）
```

**时区设置详解：**

`china_timezone` 控制备份文件和网页中显示的时间格式：

| 配置值 | 效果 | 示例 |
|--------|------|------|
| `true` | 使用中国时区 (GMT+8) | API 时间 `2025-08-11T00:00:00Z` → 显示 `2025-08-11 08:00:00` |
| `false` | 使用 UTC 时区 | API 时间 `2025-08-11T00:00:00Z` → 显示 `2025-08-11 00:00:00` |

- 默认值：`false`
- 影响范围：备份 Markdown 文件、HTML 网页、README 热力图中的所有时间显示
- 建议：中国大陆用户设置为 `true`，其他地区根据实际时区选择

#### 第 3 步：运行脚本

```bash
# 智能同步（推荐）：仅同步新增/修改内容
python main.py

# 全量同步：重新生成所有备份文件
python main.py --full-sync
```
## 🗑️ 清理已删除的帖子

### GitHub Actions 清理
1. 进入 **Actions** 标签页
2. 点击 **Manual Cleanup** → **Run workflow**

### 本地清理
```bash
# 清理模式：删除已在服务器上删除的本地备份
python main.py --cleanup
```

**注意：**
- 清理操作会永久删除本地备份文件
- 清理后需运行全量同步重新生成干净的汇总文件

## 📊 活动总结报告

工具自动生成年度发帖统计与热力图报告，包含：

- **年度发帖总数**
- **GitHub 风格热力图**：按日期显示发帖频率

报告默认生成在仓库根目录的 `README.md` 文件中。

**更新规则：**
- 全量同步时：总是重新生成报告
- 增量同步时：仅检测到新帖子时更新
- 首次运行时：自动生成初始报告

## 🔄 同步模式

### 全量同步
**触发条件：**
- 首次运行
- 手动勾选"强制全量同步"
- 同步状态文件损坏

**执行操作：**
- 清理旧备份
- 重新下载所有帖子
- 重新生成所有备份文件和报告

### 增量同步
**触发条件：**
- 非首次运行
- 未勾选"强制全量同步"
- 同步状态文件正常

**执行操作：**
- 仅下载新增帖子
- 仅更新已修改帖子
- 智能更新报告（仅当有新内容时）



## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。