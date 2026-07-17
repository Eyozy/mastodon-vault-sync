# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from src.api import fetch_mastodon_posts
from src.config import get_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


def load_runtime_config():
    # get_config() 内部已完成校验并回填默认值
    return get_config()


def resolve_runtime_paths(config):
    backup_config = config["backup"]
    backup_path = Path(backup_config["path"])
    state_file_path = Path(config["sync"]["state_file"])
    archive_file_path = backup_path / backup_config["filename"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]
    return (
        backup_config,
        backup_path,
        state_file_path,
        archive_file_path,
        posts_folder_path,
        media_folder_path,
    )


def resolve_sync_flags(archive_file_path):
    is_cleanup_mode = "--cleanup" in sys.argv
    is_cli_full_sync = "--full" in sys.argv or "--full-sync" in sys.argv
    is_action_full_sync = os.environ.get("FORCE_FULL_SYNC") == "true"
    is_first_run = not archive_file_path.exists()
    is_manual_full_sync = is_cli_full_sync or is_action_full_sync
    return {
        "is_cleanup_mode": is_cleanup_mode,
        "is_first_run": is_first_run,
        "is_full_sync": is_manual_full_sync or is_first_run,
    }


def cleanup_for_full_sync(
    state_file_path,
    archive_file_path,
    posts_folder_path,
    media_folder_path,
    is_first_run,
):
    from src.utils import safe_remove_directory, safe_remove_file

    if is_first_run:
        logging.info("🆕 检测到首次运行，将开始初始化备份...")
    else:
        logging.warning("⚠️  检测到全量同步模式，将清理目标路径下的旧备份文件...")

    if not safe_remove_file(state_file_path):
        logging.error("❌ 无法删除状态文件，但继续执行...")

    if not safe_remove_file(archive_file_path):
        logging.error("❌ 无法删除归档文件，但继续执行...")

    if not safe_remove_directory(posts_folder_path):
        logging.error("❌ 无法删除帖子文件夹，请手动检查是否有程序占用该文件夹")
        logging.error(
            "❌ 建议：关闭可能占用文件夹的程序（如文件浏览器、OneDrive 同步等）后重试"
        )
        if posts_folder_path.exists():
            logging.error("❌ 由于无法清理旧文件，为了安全起见，程序将退出")
            sys.exit(1)

    if not safe_remove_directory(media_folder_path):
        logging.error("❌ 无法删除媒体文件夹，但继续执行...")


def load_last_synced_id(state_file_path, is_full_sync):
    if is_full_sync or not state_file_path.exists():
        return None, is_full_sync

    try:
        last_synced_id = json.loads(state_file_path.read_text())["last_synced_id"]
        return last_synced_id, False
    except (json.JSONDecodeError, KeyError, OSError):
        logging.warning("⚠️ 同步状态文件格式不正确，将执行全量同步。")
        return None, True


async def collect_posts_for_sync(config, last_synced_id, is_full_sync):
    if is_full_sync:
        logging.info("🔄 智能全量同步模式，将获取所有历史帖子...")
        logging.info("⚡ 系统将智能管理 API 速率限制，可能需要一些时间完成")
        posts_to_process = await fetch_mastodon_posts(config)
        new_posts_count = len(posts_to_process)
        logging.info(f"📊 全量同步完成，共获取 {new_posts_count} 条历史帖子")
        return posts_to_process, new_posts_count

    logging.info("🔎 正在检查上次同步后的新帖子...")
    new_posts = await fetch_mastodon_posts(config, since_id=last_synced_id)
    logging.info(f"✅ 新帖子检查完成，发现 {len(new_posts)} 条新帖子")

    logging.info("🔎 正在拉取最近 5 页帖子，用于校验本地归档和清理记录...")
    recent_posts = await fetch_mastodon_posts(config, page_limit=5)
    logging.info(f"✅ 最近帖子校验数据获取完成，共 {len(recent_posts)} 条")

    posts_dict = {post["id"]: post for post in new_posts}
    for post in recent_posts:
        posts_dict[post["id"]] = post
    posts_to_process = sorted(posts_dict.values(), key=lambda post: post["created_at"])
    return posts_to_process, len(new_posts)


def write_sync_state_file(
    state_file_path, posts_to_process, last_synced_id, is_full_sync
):
    all_ids = [post["id"] for post in posts_to_process]
    if last_synced_id and not is_full_sync:
        all_ids.append(last_synced_id)
    if all_ids:
        state_file_path.write_text(
            json.dumps({"last_synced_id": max(all_ids, key=int)})
        )


async def generate_html_output(
    config, backup_path, backup_config, is_full_sync, new_posts_count, posts_to_process
):
    from src.render import generate_mastodon_html

    html_filename = backup_config.get("html_filename", "index.html")
    html_filepath = backup_path / html_filename

    needs_html = not html_filepath.exists() or is_full_sync or new_posts_count > 0
    if not needs_html:
        logging.info("✅ HTML 文件已存在且无新内容，跳过生成")
        return

    if not html_filepath.exists():
        logging.info("🌐 HTML 文件不存在，准备首次生成...")
    elif is_full_sync:
        logging.info("🔄 全量同步模式，将重新生成 HTML...")
    else:
        logging.info(f"📊 检测到 {new_posts_count} 条新帖子，需要更新 HTML...")

    # 全量同步可直接复用本次已拉取数据；增量更新仍拉全量，保证页面完整。
    if is_full_sync and posts_to_process:
        posts_for_html = posts_to_process
        logging.info(f"📊 使用全量同步数据 ({len(posts_for_html)} 条帖子)")
    else:
        logging.info("📊 正在获取所有帖子用于 HTML 生成...")
        posts_for_html = await fetch_mastodon_posts(config)
        if posts_for_html:
            logging.info(f"📊 成功获取 {len(posts_for_html)} 条帖子")
        else:
            logging.error("❌ 无法从 API 获取帖子数据")
            return

    generate_mastodon_html(posts_for_html, config, backup_path)
    logging.info(f"✅ HTML 网页已生成，包含 {len(posts_for_html)} 条嘟文")


def should_update_summary(is_full_sync, new_posts_count, backup_path, backup_config):
    summary_filepath = backup_path / backup_config["summary_filename"]
    if is_full_sync:
        return True
    if not summary_filepath.exists():
        return True
    return new_posts_count > 0


async def main_async():
    logging.info("========================================")
    logging.info(" Mastodon Sync 开始运行 (Async Mode)")
    logging.info("========================================")

    try:
        config = load_runtime_config()
    except ValueError as e:
        logging.error(f"❌ 配置验证失败：{e}")
        return
    except (FileNotFoundError, OSError) as e:
        logging.error(f"❌ 配置加载失败：{e}")
        return

    (
        backup_config,
        backup_path,
        state_file_path,
        archive_file_path,
        posts_folder_path,
        media_folder_path,
    ) = resolve_runtime_paths(config)
    base_path_str = config["backup"]["path"]
    if not os.environ.get("GITHUB_ACTIONS") and base_path_str != ".":
        logging.info(f"💾 所有备份文件将保存到指定目录：{backup_path.resolve()}")
    backup_path.mkdir(parents=True, exist_ok=True)

    sync_flags = resolve_sync_flags(archive_file_path)
    is_cleanup_mode = sync_flags["is_cleanup_mode"]
    is_first_run = sync_flags["is_first_run"]
    is_full_sync = sync_flags["is_full_sync"]
    config["is_full_sync"] = is_full_sync

    if is_cleanup_mode:
        from src.backup import cleanup_deleted_posts
        from src.render import generate_activity_summary, generate_mastodon_html

        logging.info("🧹 正在检查服务器帖子，清理本地已删除内容...")
        server_posts = await fetch_mastodon_posts(config)
        local_post_files = list(posts_folder_path.glob("*.md"))
        if local_post_files and not server_posts:
            logging.error("❌ 未获取到服务器帖子，已停止清理，避免误删本地备份。")
            return

        deleted_posts, deleted_media = cleanup_deleted_posts(
            server_posts, config, backup_path
        )
        logging.info(
            f"✅ 清理完成：删除 {deleted_posts} 个帖子文件，"
            f"删除 {deleted_media} 个媒体文件。"
        )

        generate_activity_summary(config, backup_path)
        if server_posts:
            generate_mastodon_html(server_posts, config, backup_path)
        return

    if is_full_sync:
        cleanup_for_full_sync(
            state_file_path,
            archive_file_path,
            posts_folder_path,
            media_folder_path,
            is_first_run,
        )

    last_synced_id, is_full_sync = load_last_synced_id(state_file_path, is_full_sync)
    config["is_full_sync"] = is_full_sync

    posts_to_process, new_posts_count = await collect_posts_for_sync(
        config, last_synced_id, is_full_sync
    )

    if posts_to_process:
        from src.backup import save_posts

        await save_posts(posts_to_process, config, backup_path)
        write_sync_state_file(
            state_file_path, posts_to_process, last_synced_id, is_full_sync
        )
    else:
        logging.info("✨ 没有新内容需要同步。")

    if should_update_summary(is_full_sync, new_posts_count, backup_path, backup_config):
        from src.render import generate_activity_summary

        if is_full_sync:
            logging.info("🔄 全量同步模式，生成活动总结...")
        else:
            logging.info("📊 检测到新内容，更新活动总结...")
        generate_activity_summary(config, backup_path)
    else:
        logging.info("📊 没有新内容需要更新，跳过活动总结生成。")

    try:
        await generate_html_output(
            config,
            backup_path,
            backup_config,
            is_full_sync,
            new_posts_count,
            posts_to_process,
        )
    except (OSError, ValueError) as e:
        logging.error(f"❌ HTML 网页生成失败：{e}")
    except Exception:
        logging.exception("❌ HTML 网页生成失败")

    logging.info("========================================")
    logging.info("同步完成！")
    logging.info("========================================")


def main():
    asyncio.run(main_async())


def resolve_venv_python():
    project_root = Path(__file__).resolve().parent
    venv_root = project_root / "venv"
    venv_python = (
        venv_root / "Scripts" / "python.exe"
        if sys.platform.startswith("win")
        else venv_root / "bin" / "python"
    )
    if venv_python.exists():
        return venv_python
    return None


def restart_with_venv_python():
    # 默认关闭；需要时设置 MASTODON_VAULT_SYNC_AUTO_VENV=1
    if os.environ.get("MASTODON_VAULT_SYNC_AUTO_VENV") != "1":
        return

    venv_python = resolve_venv_python()
    if not venv_python:
        return

    venv_root = venv_python.parents[1]
    if Path(sys.prefix).resolve() == venv_root.resolve():
        return

    logging.info(f"Using project venv python: {venv_python}")
    os.execv(
        str(venv_python),
        [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]],
    )


if __name__ == "__main__":
    restart_with_venv_python()

    from src.cli import main_cli

    main_cli()
