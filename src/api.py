# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

from .utils import parse_rate_limit_reset

# --- API 请求配置常量 ---
POSTS_PER_REQUEST = 40  # 每次请求的最大帖子数量 (Mastodon API 限制)
RATE_LIMIT_THRESHOLD = 10  # 速率限制安全阈值，低于此值时触发等待
DEFAULT_WAIT_TIME = 300  # 默认等待时间（秒），当无法解析速率限制重置时间时使用
REQUEST_RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1


async def _fetch_posts_page(
    session: aiohttp.ClientSession,
    api_url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], "aiohttp.typedefs.LooseHeaders"]:
    for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
        try:
            async with session.get(api_url, headers=headers, params=params) as response:
                response.raise_for_status()
                posts = await response.json()
                return posts, response.headers
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            if attempt == REQUEST_RETRY_ATTEMPTS:
                raise
            wait_time = RETRY_BASE_DELAY_SECONDS * attempt
            logging.warning(
                f"⚠️ API 请求失败，第 {attempt} 次重试前等待 {wait_time} 秒：{exc}"
            )
            await asyncio.sleep(wait_time)

    return [], {}


async def fetch_mastodon_posts(
    config: Dict[str, Any],
    since_id: Optional[str] = None,
    page_limit: Optional[int] = None,
    max_posts: Optional[int] = None,
) -> List[Dict[str, Any]]:
    mastodon_config = config["mastodon"]
    instance_url, user_id, access_token = (
        mastodon_config["instance_url"],
        mastodon_config["user_id"],
        mastodon_config["access_token"],
    )
    api_url = f"{instance_url}/api/v1/accounts/{user_id}/statuses"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "limit": POSTS_PER_REQUEST,
        "exclude_replies": "false",
        "exclude_reblogs": "true",
    }
    if since_id:
        params["since_id"] = since_id

    all_posts: List[Dict[str, Any]] = []
    page_count = 1
    requests_in_window = 0
    window_start_time = time.time()

    # 创建带 SSL 验证的 connector，防止中间人攻击
    connector = aiohttp.TCPConnector(ssl=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        while api_url:
            try:
                # 智能速率限制管理
                current_time = time.time()
                if current_time - window_start_time >= 300:  # 5 分钟窗口
                    requests_in_window = 0
                    window_start_time = current_time
                    logging.info("🔄 重置 API 调用计数器（5 分钟窗口）")

                # 检查速率限制
                if requests_in_window >= 280:  # 留 20 次缓冲
                    wait_time = 300 - (current_time - window_start_time)
                    if wait_time > 0:
                        logging.info(f"⏱️ 接近 API 限制，等待 {wait_time:.1f} 秒...")
                        # 简单的异步等待，不显示复杂进度条以免阻塞
                        await asyncio.sleep(wait_time)
                        logging.info("✅ API 限制已重置，继续获取帖子...")
                        requests_in_window = 0
                        window_start_time = time.time()

                # 每获取 100 页显示一次进度报告
                if page_count % 100 == 0 or page_count % 25 == 1:
                    logging.info(
                        f"📊 进度报告：已获取 {len(all_posts)} 条帖子，共 {page_count} 页"
                    )
                logging.info(
                    f"📄 正在获取第 {page_count} 页...（window: {requests_in_window}/300）"
                )

                posts, response_headers = await _fetch_posts_page(
                    session, api_url, headers, params
                )

                # 检查 API 返回的速率限制头
                rate_limit_remaining = int(
                    response_headers.get("X-RateLimit-Remaining", 0)
                )

                # 解析 X-RateLimit-Reset 时间戳
                reset_header = response_headers.get("X-RateLimit-Reset", "0")
                rate_limit_reset = parse_rate_limit_reset(reset_header)

                # 如果解析失败，使用默认值
                if rate_limit_reset is None:
                    rate_limit_reset = int(time.time()) + DEFAULT_WAIT_TIME

                # 获取 Link header 用于分页
                link_header = response_headers.get("Link", "")

                if not posts:
                    break
                all_posts.extend(posts)
                requests_in_window += 1

                # 检查是否达到限制
                if page_limit and page_count >= page_limit:
                    break
                if max_posts and len(all_posts) >= max_posts:
                    all_posts = all_posts[:max_posts]
                    break

                # 如果剩余调用次数很少，等待重置
                current_time = time.time()
                if rate_limit_remaining < RATE_LIMIT_THRESHOLD:
                    reset_wait = max(0, rate_limit_reset - current_time)
                    if reset_wait > 0 and reset_wait < 300:
                        logging.info(
                            f"⏱️ API 调用即将用完，等待 {reset_wait:.1f} 秒重置..."
                        )
                        await asyncio.sleep(reset_wait)
                        logging.info("✅ API 限制已重置，继续获取帖子...")
                        requests_in_window = 0

                # 解析下一页链接
                # aiohttp 需要手动解析 Link header，或者使用 helper
                # 这里简单解析
                next_url = None
                if 'rel="next"' in link_header:
                    links = link_header.split(",")
                    for link in links:
                        if 'rel="next"' in link:
                            next_url = link[link.find("<") + 1 : link.find(">")]
                            break

                api_url = next_url
                # 后续请求不需要 params 中的 since_id，因为 url 已经包含了
                params = {}
                page_count += 1

            except aiohttp.ClientError as e:
                logging.error(f"❌ API 请求失败：{e}")
                return []
            except Exception as e:
                logging.error(f"❌ 发生未知错误：{e}")
                return []

    all_posts.reverse()
    logging.info(f"✅ 成功获取 {len(all_posts)} 条帖子，共调用 {page_count-1} 次 API")
    return all_posts
