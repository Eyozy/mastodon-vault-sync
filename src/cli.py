# -*- coding: utf-8 -*-
"""命令行接口"""
import getpass
import json
import sys
from pathlib import Path

from src import __version__

try:
    import colorama
except ImportError:
    colorama = None

if colorama:
    colorama.init(autoreset=True)

PYTHON_COMMAND = "python" if sys.platform.startswith("win") else "python3"


def init_config():
    """交互式配置向导"""
    print("🎉 欢迎使用 Mastodon Vault Sync!\n")

    # 检查是否已存在配置文件
    config_path = Path("config.yaml")
    if config_path.exists():
        overwrite = input("⚠️  配置文件已存在，是否覆盖？(y/N): ").strip().lower()
        if overwrite != "y":
            print("❌ 已取消")
            return

    # 获取实例地址
    print("📍 步骤 1/4: Mastodon 实例地址")
    instance_url = input("  请输入实例地址 (例如：https://mastodon.social): ").strip()
    if not instance_url:
        print("❌ 实例地址不能为空")
        return

    # 获取用户 ID
    print("\n👤 步骤 2/4: 用户 ID")
    print("  💡 如何获取？")
    print(f"     访问：{instance_url}/api/v1/accounts/lookup?acct=你的用户名")
    print('     复制返回 JSON 中的 "id" 字段 (一串数字）')
    user_id = input("  请输入用户 ID: ").strip()
    if not user_id:
        print("❌ 用户 ID 不能为空")
        return

    # 获取访问令牌
    print("\n🔑 步骤 3/4: 访问令牌")
    print("  💡 如何获取？")
    print("     1. 登录 Mastodon")
    print("     2. 进入 首选项 -> 开发 -> 新建应用")
    print("     3. 权限只勾选 read:statuses")
    print("     4. 创建后复制 access token")
    access_token = getpass.getpass("  请输入访问令牌 (输入时不显示): ").strip()
    if not access_token:
        print("❌ 访问令牌不能为空")
        return

    # 获取备份路径
    print("\n💾 步骤 4/4: 备份路径")
    backup_path = input("  备份路径 [默认：./backup]: ").strip() or "./backup"

    # 生成配置文件
    config_content = f"""mastodon:
  instance_url: "{instance_url}"
  user_id: {user_id}
  access_token: "{access_token}"

backup:
  path: "{backup_path}"
  posts_folder: "mastodon"
  filename: "archive.md"
  media_folder: "media"
  summary_filename: "README.md"
  html_filename: "index.html"

sync:
  state_file: "sync_state.json"
  china_timezone: false
"""

    try:
        config_path.write_text(config_content, encoding="utf-8")
        print(f"\n✅ 配置已保存到：{config_path.resolve()}")
        print("\n下一步运行：")
        print(f"  {PYTHON_COMMAND} main.py sync")
    except Exception as e:
        print(f"\n❌ 保存配置失败：{e}")


def check_config():
    """检查配置有效性"""
    print("🔍 正在检查配置...\n")

    # 检查配置文件
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ 配置文件不存在：config.yaml")
        print("\n请运行以下命令创建配置：")
        print(f"  {PYTHON_COMMAND} main.py init")
        return

    print("✅ 配置文件：config.yaml 存在")

    # 加载并验证配置（get_config 内部已调用 validate_config）
    try:
        from src.config import get_config

        config = get_config()
        print("✅ 配置格式：正确")
    except Exception as e:
        print_config_error(e)
        return

    # 显示配置信息
    instance_url = config["mastodon"]["instance_url"]
    user_id = config["mastodon"]["user_id"]
    backup_path = Path(config["backup"]["path"])

    print(f"✅ 实例地址：{instance_url}")
    print(f"✅ 用户 ID: {user_id}")
    print(f"✅ 备份路径：{backup_path.resolve()}")
    if is_cloud_storage_path(backup_path):
        print("⚠️  检测到云盘路径；如遇权限错误，请确认 OneDrive/Obsidian 未占用该目录")

    print("\n🎉 配置正确！可以开始同步了")
    print(f"  {PYTHON_COMMAND} main.py sync")


def is_cloud_storage_path(path):
    """判断路径是否位于常见云盘同步目录"""
    path_text = str(path.expanduser())
    return any(
        marker in path_text
        for marker in ("CloudStorage", "OneDrive", "iCloud", "Dropbox")
    )


def print_cloud_storage_hint(path):
    print(f"⚠️  无法访问：{path}")
    print("   这通常是云盘同步、Obsidian、Finder 或 macOS 权限限制导致的。")
    print("   建议先关闭占用该目录的程序，或把备份路径换到普通本地目录后重试。")


def print_config_error(error):
    print(f"❌ 配置检查失败：{error}")
    if isinstance(error, ModuleNotFoundError):
        print("\n这不是 config.yaml 写错，更像是当前 Python 环境依赖损坏或未安装。")
        print("请优先使用项目虚拟环境运行：")
        print("  venv/bin/python main.py")
        return

    print("\n请检查配置文件或重新运行：")
    print(f"  {PYTHON_COMMAND} main.py init")


def show_status():
    """显示同步状态"""
    print("📊 同步状态\n")

    try:
        from src.config import get_config

        config = get_config()
        state_file = Path(config["sync"]["state_file"])
    except Exception:
        state_file = Path("sync_state.json")
        config = None

    if not state_file.exists():
        print("⚠️  尚未进行过同步")
        print("\n运行以下命令开始首次同步：")
        print(f"  {PYTHON_COMMAND} main.py sync --full")
        return

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        last_id = state.get("last_synced_id", "N/A")
        print(f"上次同步 ID: {last_id}")

    except Exception as e:
        print(f"❌ 读取状态失败：{e}")
        return

    if not config:
        return

    backup_path = Path(config["backup"]["path"])
    posts_folder = backup_path / config["backup"]["posts_folder"]
    media_folder = backup_path / config["backup"]["media_folder"]

    try:
        post_count = (
            sum(1 for _ in posts_folder.glob("*.md")) if posts_folder.exists() else 0
        )
        print(f"帖子总数：{post_count} 条")
    except PermissionError:
        print_cloud_storage_hint(posts_folder)
    except OSError as e:
        print(f"⚠️  无法读取帖子目录：{e}")

    try:
        media_count = 0
        media_size = 0
        if media_folder.exists():
            for f in media_folder.iterdir():
                if f.is_file():
                    media_count += 1
                    media_size += f.stat().st_size
        print(f"媒体文件：{media_count} 个 ({media_size / 1024 / 1024:.1f} MB)")
    except PermissionError:
        print_cloud_storage_hint(media_folder)
    except OSError as e:
        print(f"⚠️  无法读取媒体目录：{e}")


def show_help():
    """显示帮助信息"""
    print(
        f"""Mastodon Vault Sync v{__version__}

用法：{PYTHON_COMMAND} main.py <命令> [选项]

命令：
  menu              打开交互式菜单（无参数默认进入）
  init              初始化配置
  sync              同步帖子（增量）
  sync --full       全量同步
  cleanup           清理已删除的帖子
  status            查看同步状态
  check             检查配置
  version           显示版本号
  help              显示此帮助

示例：
  {PYTHON_COMMAND} main.py               # 打开交互式菜单
  {PYTHON_COMMAND} main.py menu          # 打开交互式菜单
  {PYTHON_COMMAND} main.py init          # 首次使用，创建配置
  {PYTHON_COMMAND} main.py check         # 检查配置是否正确
  {PYTHON_COMMAND} main.py sync --full   # 首次同步，获取所有历史帖子
  {PYTHON_COMMAND} main.py sync          # 日常增量同步
  {PYTHON_COMMAND} main.py status        # 查看同步状态
  {PYTHON_COMMAND} main.py cleanup       # 清理已删除的帖子

更多信息：https://github.com/Eyozy/mastodon-vault-sync
"""
    )


def run_sync(full_sync=False):
    """执行同步"""
    sys.argv = ["main.py", "--full-sync"] if full_sync else ["main.py"]
    from main import main

    main()


def run_cleanup():
    """执行清理"""
    sys.argv = ["main.py", "--cleanup"]
    from main import main

    main()


def show_menu():
    """显示交互式菜单"""
    print(f"\n{'=' * 42}")
    print(f"  Mastodon Vault Sync v{__version__}")
    print(f"{'=' * 42}")
    print("请选择要执行的操作：")
    print("  1  初始化配置")
    print("  2  检查配置")
    print("  3  查看同步状态")
    print("  4  日常增量同步")
    print("  5  首次/全量同步")
    print("  6  清理已删除的帖子")
    print("  7  显示帮助")
    print("  0  退出")
    print(f"{'-' * 42}")


def run_menu_action(action):
    try:
        action()
    except PermissionError as e:
        print(f"\n❌ 权限错误：{e}")
        print("   请检查备份目录是否被 OneDrive、Obsidian 或系统权限限制占用。")
    except KeyboardInterrupt:
        print("\n已取消当前操作")
    except Exception as e:
        print(f"\n❌ 操作失败：{e}")


def interactive_menu():
    """交互式命令菜单"""
    actions = {
        "1": init_config,
        "2": check_config,
        "3": show_status,
        "4": lambda: run_sync(full_sync=False),
        "5": lambda: run_sync(full_sync=True),
        "6": run_cleanup,
        "7": show_help,
    }

    while True:
        show_menu()
        choice = input("请输入选项编号: ").strip()

        if choice == "0":
            print("已退出")
            return

        action = actions.get(choice)
        if not action:
            print("❌ 无效选项，请重新输入\n")
            continue

        run_menu_action(action)
        input("\n按回车键返回菜单...")


def main_cli():
    """CLI 入口"""
    args = sys.argv[1:]

    if not args:
        interactive_menu()
        return

    if args[0] in ["help", "--help", "-h"]:
        show_help()
        return

    command = args[0]

    # 处理各种命令
    if command == "version":
        print(f"Mastodon Vault Sync v{__version__}")
    elif command == "menu":
        interactive_menu()
    elif command == "init":
        init_config()
    elif command == "check":
        check_config()
    elif command == "status":
        show_status()
    elif command == "sync":
        run_sync(full_sync="--full" in args)
    elif command == "cleanup":
        run_cleanup()
    else:
        print(f"❌ 未知命令：{command}\n")
        show_help()
