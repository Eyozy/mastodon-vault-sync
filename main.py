# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from src.api import fetch_mastodon_posts
from src.backup import save_posts
from src.config import get_config, validate_config
from src.render import generate_activity_summary, generate_mastodon_html
from src.utils import safe_remove_directory, safe_remove_file

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


def should_update_summary(is_full_sync, new_posts_count, backup_path, backup_config):
    """
    判断是否需要更新活动总结
    """
    summary_filepath = backup_path / backup_config["summary_filename"]

    # 全量同步时总是更新
    if is_full_sync:
        return True

    # 首次运行时更新
    if not summary_filepath.exists():
        return True

    # 有新帖子时更新
    if new_posts_count > 0:
        return True

    return False


async def main_async():
    logging.info("========================================")
    logging.info(" Mastodon Sync 开始运行 (Async Mode)")
    logging.info("========================================")

    try:
        config = get_config()

        # 验证配置
        validate_config(config)
    except ValueError as e:
        logging.error(f"❌ 配置验证失败：{e}")
        return
    except Exception as e:
        # get_config 可能会抛出其他异常（如从 yaml 加载时）
        logging.error(f"❌ 初始化失败：{e}")
        return

    # 根据配置确定最终的备份路径
    base_path_str = config["backup"]["path"]
    backup_path = Path(base_path_str)
    # 仅在本地运行时，如果路径不是默认的"."，才显示提示信息
    if not os.environ.get("GITHUB_ACTIONS") and base_path_str != ".":
        logging.info(f"💾 所有备份文件将保存到指定目录：{backup_path.resolve()}")
    backup_path.mkdir(parents=True, exist_ok=True)

    # 状态文件总是和脚本放在一起（项目根目录），不随备份路径改变
    state_file_path = Path(config["sync"]["state_file"])

    backup_config = config["backup"]
    archive_file_path = backup_path / backup_config["filename"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]

    is_cleanup_mode = "--cleanup" in sys.argv
    is_cli_full_sync = "--full" in sys.argv or "--full-sync" in sys.argv
    is_action_full_sync = os.environ.get("FORCE_FULL_SYNC") == "true"
    is_first_run = not archive_file_path.exists()
    is_manual_full_sync = is_cli_full_sync or is_action_full_sync or is_cleanup_mode
    is_full_sync = is_manual_full_sync or is_first_run
    config["is_full_sync"] = is_full_sync

    if is_cleanup_mode:
        logging.info(
            "🧹 检测到 cleanup 模式，将执行全量重建以清理已删除的帖子和媒体文件..."
        )

    if is_full_sync:
        if is_first_run:
            logging.info("🆕 检测到首次运行，将开始初始化备份...")
        else:
            logging.warning("⚠️  检测到全量同步模式，将清理目标路径下的旧备份文件...")

        # 状态文件在项目目录，也要清理
        if not safe_remove_file(state_file_path):
            logging.error("❌ 无法删除状态文件，但继续执行...")

        if not safe_remove_file(archive_file_path):
            logging.error("❌ 无法删除归档文件，但继续执行...")

        if not safe_remove_directory(posts_folder_path):
            logging.error("❌ 无法删除帖子文件夹，请手动检查是否有程序占用该文件夹")
            logging.error(
                "❌ 建议：关闭可能占用文件夹的程序（如文件浏览器、OneDrive 同步等）后重试"
            )
            # 选择性退出，因为无法删除文件夹可能会导致后续操作失败
            if posts_folder_path.exists():
                logging.error("❌ 由于无法清理旧文件，为了安全起见，程序将退出")
                sys.exit(1)

        if not safe_remove_directory(media_folder_path):
            logging.error("❌ 无法删除媒体文件夹，但继续执行...")

    last_synced_id = None
    if not is_full_sync and state_file_path.exists():
        try:
            last_synced_id = json.loads(state_file_path.read_text())["last_synced_id"]
        except (json.JSONDecodeError, KeyError):
            logging.warning("⚠️ 同步状态文件格式不正确，将执行全量同步。")
            is_full_sync = True
            config["is_full_sync"] = True

    if is_full_sync:
        # 智能全量同步：充分利用 API 限制获取所有帖子
        # 无页数限制，通过智能速率管理安全获取所有历史帖子
        logging.info("🔄 智能全量同步模式，将获取所有历史帖子...")
        logging.info("⚡ 系统将智能管理 API 速率限制，可能需要一些时间完成")
        posts_to_process = await fetch_mastodon_posts(config)
        all_posts_from_server_for_sync = posts_to_process
        new_posts_count = len(posts_to_process)
        logging.info(f"📊 全量同步完成，共获取 {new_posts_count} 条历史帖子")
    else:
        new_posts = await fetch_mastodon_posts(config, since_id=last_synced_id)
        # 获取更多帖子用于编辑检测（5 页，200 条帖子），覆盖过去 1-2 周的编辑
        recent_posts = await fetch_mastodon_posts(config, page_limit=5)
        all_posts_from_server_for_sync = recent_posts
        posts_dict = {p["id"]: p for p in new_posts}
        for p in recent_posts:
            posts_dict[p["id"]] = p
        posts_to_process = sorted(
            list(posts_dict.values()), key=lambda p: p["created_at"]
        )
        new_posts_count = len(new_posts)

    if posts_to_process:
        await save_posts(
            posts_to_process, config, all_posts_from_server_for_sync, backup_path
        )
        all_ids = [p["id"] for p in posts_to_process]
        if last_synced_id and not is_full_sync:
            all_ids.append(last_synced_id)
        if all_ids:
            state_file_path.write_text(
                json.dumps({"last_synced_id": max(all_ids, key=int)})
            )
    else:
        logging.info("✨ 没有新内容需要同步。")

    # 统一的活动总结更新逻辑：智能同步和全量同步都会更新统计
    if should_update_summary(is_full_sync, new_posts_count, backup_path, backup_config):
        if is_full_sync:
            logging.info("🔄 全量同步模式，生成活动总结...")
        else:
            logging.info("📊 检测到新内容，更新活动总结...")
        generate_activity_summary(config, backup_path)
    else:
        logging.info("📊 没有新内容需要更新，跳过活动总结生成。")

    # 生成 HTML 网页 - 智能检测是否需要更新
    try:
        html_filename = backup_config.get("html_filename", "index.html")
        html_filepath = backup_path / html_filename
        should_generate_html = False
        posts_for_html = None

        # 判断是否需要生成 HTML
        if not html_filepath.exists():
            logging.info("🌐 HTML 文件不存在，准备首次生成...")
            should_generate_html = True
        elif is_full_sync:
            logging.info("🔄 全量同步模式，将重新生成 HTML...")
            should_generate_html = True
        elif new_posts_count > 0:
            logging.info(f"📊 检测到 {new_posts_count} 条新帖子，需要更新 HTML...")
            should_generate_html = True
        else:
            logging.info("✅ HTML 文件已存在且无新内容，跳过生成")

        # 如果需要生成 HTML，获取所有帖子数据
        if should_generate_html:
            if is_full_sync and posts_to_process:
                # 全量同步时，posts_to_process 已包含所有帖子
                logging.info(f"📊 使用全量同步数据 ({len(posts_to_process)} 条帖子)")
                posts_for_html = posts_to_process
            else:
                # 增量同步或全量同步失败时，重新获取所有帖子
                logging.info("📊 正在获取所有帖子用于 HTML 生成...")
                # 注意：这里也需要 await，因为 fetch_mastodon_posts 是异步的
                all_posts_for_html = await fetch_mastodon_posts(config)
                if all_posts_for_html:
                    logging.info(f"📊 成功获取 {len(all_posts_for_html)} 条帖子")
                    posts_for_html = all_posts_for_html
                else:
                    logging.error("❌ 无法从 API 获取帖子数据")

            # 生成 HTML
            if posts_for_html:
                generate_mastodon_html(posts_for_html, config, backup_path)
                logging.info(f"✅ HTML 网页已生成，包含 {len(posts_for_html)} 条嘟文")
            else:
                logging.error("❌ 没有可用的帖子数据，无法生成 HTML")

    except Exception as e:
        logging.error(f"❌ HTML 网页生成失败：{e}")
        import traceback

        logging.error(traceback.format_exc())

    logging.info("========================================")
    logging.info("同步完成！")
    logging.info("========================================")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    # 统一使用 CLI 入口
    if len(sys.argv) > 1:
        from src.cli import main_cli

        main_cli()
    else:
        # 无参数时显示帮助
        from src.cli import show_help

        show_help()
