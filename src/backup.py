# -*- coding: utf-8 -*-
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
import yaml
from tqdm.asyncio import tqdm_asyncio

from .render import format_post_for_single_file
from .utils import get_timezone_aware_datetime

MEDIA_DOWNLOAD_CONCURRENCY = 8


async def download_media(
    session: aiohttp.ClientSession, media_item: Dict[str, Any], media_folder_path: Path
) -> Optional[str]:
    try:
        url = media_item["url"]
        original_filename = Path(urlparse(url).path).name
        local_filename = f"{media_item['id']}-{original_filename}"
        local_file_path = media_folder_path / local_filename

        if local_file_path.exists():
            return local_filename

        async with session.get(url) as response:
            response.raise_for_status()
            async with aiofiles.open(local_file_path, "wb") as f:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk:
                        break
                    await f.write(chunk)

        return local_filename
    except Exception as e:
        logging.error(f"❌ 下载媒体文件失败：{media_item.get('url')} - {e}")
        return None


async def download_all_media(
    media_items: List[Dict[str, Any]],
    media_folder_path: Path,
    is_full_sync: bool = False,
) -> Dict[str, str]:
    """并发下载所有媒体文件"""
    media_file_map = {}
    if not media_items:
        return media_file_map

    media_folder_path.mkdir(parents=True, exist_ok=True)

    # 统计需要下载的文件数量
    files_to_download = 0
    for media in media_items:
        url = media["url"]
        original_filename = Path(urlparse(url).path).name
        local_filename = f"{media['id']}-{original_filename}"
        local_file_path = media_folder_path / local_filename
        if not local_file_path.exists():
            files_to_download += 1

    # 根据同步类型显示不同的日志信息
    if is_full_sync:
        logging.info(f"⬇️  开始并发下载 {len(media_items)} 个媒体文件...")
    else:
        if files_to_download > 0:
            logging.info(
                f"⬇️  正在下载新增的 {files_to_download} 个媒体文件（共 {len(media_items)} 个）..."
            )
        else:
            logging.info("✅ 所有媒体文件已存在，无需下载")

    # 创建带 SSL 验证的 connector，防止中间人攻击
    connector = aiohttp.TCPConnector(ssl=True)
    semaphore = asyncio.Semaphore(MEDIA_DOWNLOAD_CONCURRENCY)

    async def download_with_limit(
        session: aiohttp.ClientSession, media_item: Dict[str, Any]
    ) -> Optional[str]:
        async with semaphore:
            return await download_media(session, media_item, media_folder_path)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [download_with_limit(session, media_item) for media_item in media_items]

        # 使用 tqdm 显示下载进度
        results = await tqdm_asyncio.gather(*tasks, desc="Downloading Media")

        for media, local_filename in zip(media_items, results):
            if local_filename:
                media_file_map[media["id"]] = local_filename

    return media_file_map


def _build_archive_entry_from_post_file(
    post_file_path: Path, media_folder_name: str
) -> Optional[Dict[str, Any]]:
    try:
        content = post_file_path.read_text(encoding="utf-8")
    except OSError as exc:
        logging.error(f"❌ 读取帖子文件失败 {post_file_path.name}: {exc}")
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        logging.warning(
            f"⚠️ 帖子文件 frontmatter 格式无效，已跳过：{post_file_path.name}"
        )
        return None

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
        created_at = datetime.strptime(frontmatter["createdAt"], "%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        logging.warning(f"⚠️ 无法解析帖子文件 {post_file_path.name}: {exc}")
        return None

    body = parts[2].strip()
    body = body.replace("../media/", f"{media_folder_name}/")
    body = body.replace("\n## 附件\n", "\n\n", 1)

    post_type = frontmatter.get("type", "toot")
    is_reply = post_type == "reply"
    icon = "💬" if is_reply else "📝"
    label = "回复" if is_reply else "嘟文"
    source_label = "**回复嘟文**" if is_reply else "**原始嘟文**"
    source_url = frontmatter.get("source", "")

    archive_content = (
        f"## {created_at.strftime('%H:%M')} {icon} {label}\n\n"
        f"**内容**：{body}\n\n"
        f"{source_label}：{source_url}\n\n---"
    )
    return {
        "date": created_at.strftime("%Y-%m-%d"),
        "created_at": created_at,
        "content": archive_content,
    }


def _rebuild_archive_from_post_files(
    posts_folder_path: Path, archive_file_path: Path, media_folder_name: str
) -> None:
    rebuilt_posts_by_day = defaultdict(list)

    for post_file_path in sorted(posts_folder_path.glob("*.md")):
        archive_entry = _build_archive_entry_from_post_file(
            post_file_path, media_folder_name
        )
        if archive_entry is None:
            continue
        rebuilt_posts_by_day[archive_entry["date"]].append(archive_entry)

    final_content = ""
    for date_str in sorted(rebuilt_posts_by_day.keys(), reverse=True):
        final_content += f"# {date_str}\n\n"
        day_posts = sorted(
            rebuilt_posts_by_day[date_str],
            key=lambda post: post["created_at"],
            reverse=True,
        )
        final_content += "\n\n".join(post["content"] for post in day_posts) + "\n\n"

    archive_file_path.write_text(final_content, encoding="utf-8")


def _sync_posts_for_archive(
    posts_to_update: List[Dict[str, Any]],
    posts_folder_path: Path,
    backup_config: Dict[str, Any],
    sync_config: Dict[str, Any],
    media_file_map: Dict[str, str],
) -> None:
    posts_folder_path.mkdir(parents=True, exist_ok=True)

    for post in posts_to_update:
        local_dt = get_timezone_aware_datetime(
            post["created_at"], sync_config["china_timezone"]
        )
        filename = f"{local_dt.strftime('%Y-%m-%d_%H%M%S')}_{post['id']}.md"
        file_path = posts_folder_path / filename
        new_content = format_post_for_single_file(
            post,
            backup_config["media_folder"],
            media_file_map,
            sync_config["china_timezone"],
        )
        if file_path.exists():
            try:
                existing_content = file_path.read_text(encoding="utf-8")
                if existing_content == new_content:
                    continue
            except OSError:
                pass
        file_path.write_text(new_content, encoding="utf-8")


def update_archive_file(
    posts_to_update: List[Dict[str, Any]],
    config: Dict[str, Any],
    all_posts_from_server: List[Dict[str, Any]],
    backup_path: Path,
) -> None:
    backup_config = config["backup"]
    media_folder_name = backup_config["media_folder"]
    archive_filename = backup_config["filename"]
    posts_folder_name = backup_config.get("posts_folder", "mastodon")
    archive_file_path = backup_path / archive_filename
    posts_folder_path = backup_path / posts_folder_name

    _ = all_posts_from_server
    _sync_posts_for_archive(
        posts_to_update,
        posts_folder_path,
        backup_config,
        config["sync"],
        config.get("media_file_map", {}),
    )
    logging.info("📝 正在基于本地单帖文件重建归档，确保增量同步不丢历史...")
    _rebuild_archive_from_post_files(
        posts_folder_path, archive_file_path, media_folder_name
    )
    logging.info(f"✍️  已更新归档文件：{archive_file_path}")


async def save_posts(
    posts: List[Dict[str, Any]],
    config: Dict[str, Any],
    all_posts_from_server: List[Dict[str, Any]],
    backup_path: Path,
) -> None:
    backup_config = config["backup"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]

    # 收集所有需要下载的媒体
    all_media_items = []
    for post in posts:
        if post.get("media_attachments"):
            all_media_items.extend(post["media_attachments"])

    # 并发下载媒体
    media_file_map = await download_all_media(
        all_media_items, media_folder_path, config.get("is_full_sync", False)
    )
    config["media_file_map"] = media_file_map

    posts_folder_path.mkdir(parents=True, exist_ok=True)

    logging.info(f"📄 正在写入 {len(posts)} 个帖子文件...")

    async for post in async_iter(posts):
        local_dt = get_timezone_aware_datetime(
            post["created_at"], config["sync"]["china_timezone"]
        )
        filename = f"{local_dt.strftime('%Y-%m-%d_%H%M%S')}_{post['id']}.md"
        file_path = posts_folder_path / filename
        new_content = format_post_for_single_file(
            post,
            backup_config["media_folder"],
            media_file_map,
            config["sync"]["china_timezone"],
        )

        # 使用 aiofiles 异步写入
        if not file_path.exists():
            should_write = True
        else:
            # 读取现有文件比较内容（异步读取）
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    existing_content = await f.read()
                should_write = existing_content != new_content
            except Exception:
                should_write = True

        if should_write:
            try:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(new_content)
                # logging.info(f"📄 已备份/更新：{filename}") # 减少日志输出，避免刷屏
            except IOError as e:
                logging.error(f"❌ 无法写入文件 {file_path}: {e}")

    # 所有单帖文件落盘后，再统一重建归档文件
    update_archive_file(posts, config, all_posts_from_server, backup_path)

    logging.info("✅ 所有帖子文件写入完成")


async def async_iter(iterable):
    """辅助函数：将同步可迭代对象转换为异步迭代器"""
    for item in iterable:
        yield item
