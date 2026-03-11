# -*- coding: utf-8 -*-
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
from tqdm.asyncio import tqdm_asyncio

from .render import format_post_for_single_file, format_single_post_for_archive
from .utils import get_timezone_aware_datetime


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
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for media in media_items:
            task = download_media(session, media, media_folder_path)
            tasks.append(task)

        # 使用 tqdm 显示下载进度
        results = await tqdm_asyncio.gather(*tasks, desc="Downloading Media")

        for media, local_filename in zip(media_items, results):
            if local_filename:
                media_file_map[media["id"]] = local_filename

    return media_file_map


def update_archive_file(
    posts_to_update: List[Dict[str, Any]],
    config: Dict[str, Any],
    all_posts_from_server: List[Dict[str, Any]],
    backup_path: Path,
) -> None:
    # 归档文件更新依然是文件 IO 密集型，且需要保持顺序，暂保持同步或放入线程池
    # 为简单起见，这里保持同步，因为它只处理文本追加
    backup_config = config["backup"]
    media_folder_name, archive_filename = (
        backup_config["media_folder"],
        backup_config["filename"],
    )
    archive_file_path = backup_path / archive_filename
    existing_posts_by_id = {}
    if archive_file_path.exists():
        with open(archive_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for block in content.split("---\n"):
            if block.strip() and (
                match := re.search(r"https://[^\/]+\/[^\/]+\/(\d+)", block)
            ):
                existing_posts_by_id[match.group(1)] = block
    for post in posts_to_update:
        existing_posts_by_id[post["id"]] = format_single_post_for_archive(
            post,
            media_folder_name,
            config["media_file_map"],
            config["sync"]["china_timezone"],
        ).strip()

    # 编辑检测范围
    logging.info("📝 编辑检测范围：最近 200 条帖子，覆盖约 1-2 周内的编辑更新")
    rebuilt_posts_by_day = defaultdict(list)
    all_posts_dict = {p["id"]: p for p in all_posts_from_server}

    for post_id, content in existing_posts_by_id.items():
        if post_data := all_posts_dict.get(post_id):
            local_dt = get_timezone_aware_datetime(
                post_data["created_at"], config["sync"]["china_timezone"]
            )
            rebuilt_posts_by_day[local_dt.strftime("%Y-%m-%d")].append(
                {"content": content, "created_at": post_data["created_at"]}
            )

    final_content = ""
    for date_str in sorted(rebuilt_posts_by_day.keys(), reverse=True):
        final_content += f"# {date_str}\n\n"
        day_posts = sorted(
            rebuilt_posts_by_day[date_str], key=lambda p: p["created_at"], reverse=True
        )
        final_content += "\n".join([p["content"] for p in day_posts]) + "\n\n"

    with open(archive_file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
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

    # 更新归档文件（同步操作）
    update_archive_file(posts, config, all_posts_from_server, backup_path)

    # 异步写入单条帖子文件
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

    logging.info("✅ 所有帖子文件写入完成")


async def async_iter(iterable):
    """辅助函数：将同步可迭代对象转换为异步迭代器"""
    for item in iterable:
        yield item
