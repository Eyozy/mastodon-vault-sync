# -*- coding: utf-8 -*-
import base64
import html
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from ..utils import get_timezone_aware_datetime

REMOTE_ASSET_TIMEOUT = 10


def load_css_styles() -> str:
    """
    从外部文件加载 CSS 样式
    """
    try:
        current_dir = Path(__file__).resolve().parent.parent
        css_file = current_dir / "assets" / "style.css"

        if css_file.exists():
            with open(css_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logging.warning(f"CSS 文件不存在于 {css_file}，使用默认样式")
            return get_default_css()
    except OSError as e:
        logging.error(f"读取 CSS 文件失败：{e}，使用默认样式")
        return get_default_css()


def load_javascript() -> str:
    """
    加载 JS 脚本
    """
    try:
        current_dir = Path(__file__).resolve().parent.parent
        js_file = current_dir / "assets" / "script.js"

        if js_file.exists():
            with open(js_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logging.warning("JS 文件不存在")
            return ""
    except OSError as e:
        logging.error(f"读取 JS 文件失败：{e}")
        return ""


def get_default_css() -> str:
    """
    返回默认的内联 CSS（作为后备）
    """
    return """
    /* 基础样式后备方案 */
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; }
    .status { background: white; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
    """


def _strip_html_tags(value: str) -> str:
    return re.sub(r"<[^<]+?>", "", value).strip()


def _escape_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _serialize_posts_json(posts_data: List[Dict[str, Any]]) -> str:
    return json.dumps(posts_data, ensure_ascii=False).replace("</", "<\\/")


def validate_post_data(post_data: Dict[str, Any]) -> bool:
    """
    验证帖子数据的安全性
    """
    try:
        # 验证必需字段
        required_fields = ["id", "content", "created_at", "account"]
        for field in required_fields:
            if field not in post_data:
                raise ValueError(f"帖子数据缺少必需字段：{field}")

        # 验证 ID 格式（应该是数字字符串）
        try:
            int(post_data["id"])
        except (ValueError, TypeError):
            raise ValueError("帖子 ID 格式无效")

        # 验证内容长度，防止过长的内容
        if len(str(post_data["content"])) > 100000:  # 100KB 限制
            raise ValueError("帖子内容过长，可能存在安全隐患")

        # 验证创建时间格式
        if not isinstance(post_data["created_at"], str):
            raise ValueError("创建时间格式无效")

        # 验证账户信息
        if "account" in post_data and post_data["account"]:
            account = post_data["account"]
            if "display_name" in account and len(str(account["display_name"])) > 1000:
                raise ValueError("用户显示名称过长")

        return True

    except (ValueError, TypeError) as e:
        logging.warning(f"帖子数据验证失败：{e}")
        return False


def generate_mastodon_html(
    posts: List[Dict[str, Any]], config: Dict[str, Any], backup_path: Path
) -> None:
    """生成单文件 HTML 网页，复刻 Mastodon 界面"""
    backup_config = config["backup"]
    html_filename = backup_config.get("html_filename", "index.html")
    html_filepath = backup_path / html_filename
    media_folder = backup_config["media_folder"]

    logging.info("正在生成 Mastodon HTML 网页...")

    # 提取用户信息
    if posts:
        user = posts[0]["account"]
        username = user["username"]
        display_name = user.get("display_name", username)
        avatar = user["avatar"]
        user_id = user["id"]
        # 从 URL 中提取实例名称
        user_url = user["url"]
        account_url = user_url
        instance_name = (
            user_url.split("//")[1].split("/")[0] if "//" in user_url else ""
        )
        # 获取用户简介
        user_bio = user.get("note", "")  # note 字段包含用户的简介
        # 保存用户信息到配置中，供热力图使用
        config["username"] = username
        config["instance"] = instance_name
        # 获取用户背景图片
        header = user.get("header", "")
        if header:
            header_filename = f"header-{user_id}.jpg"
            local_header_path = f"{media_folder}/{header_filename}"

            # 下载背景图片
            try:
                header_response = requests.get(
                    header, stream=True, timeout=REMOTE_ASSET_TIMEOUT
                )
                if header_response.status_code == 200:
                    header_path = backup_path / media_folder / header_filename
                    header_path.parent.mkdir(exist_ok=True)
                    with open(header_path, "wb") as f:
                        for chunk in header_response.iter_content(1024):
                            f.write(chunk)
                    background_image = local_header_path
                else:
                    background_image = ""
            except (requests.RequestException, OSError) as e:
                logging.warning(f"下载背景图片失败：{e}")
                background_image = ""
        else:
            background_image = ""
    else:
        username = "unknown"
        display_name = "Unknown User"
        avatar = ""
        user_id = "unknown"
        account_url = ""
        instance_name = ""
        background_image = ""
        user_bio = ""

    # 提取统计数据
    total_posts = len(posts)
    followers_count = posts[0]["account"]["followers_count"] if posts else 0
    following_count = posts[0]["account"]["following_count"] if posts else 0

    # 转换帖子数据为 JSON
    posts_data = []
    for post in posts:
        # 验证帖子数据安全性
        if not validate_post_data(post):
            logging.warning(f"跳过无效的帖子数据，ID: {post.get('id', 'unknown')}")
            continue
        # 处理媒体附件
        media_items = []
        for media in post.get("media_attachments", []):
            media_filename = f"{media['id']}-{Path(urlparse(media['url']).path).name}"
            media_items.append(
                {
                    "id": media["id"],
                    "type": media["type"],
                    "url": f"{media_folder}/{media_filename}",
                    "description": media.get("description", ""),
                    "preview_url": media.get("preview_url", ""),
                }
            )

        # 处理内容 HTML 和表情符号
        content_html = post.get("content", "")

        # 处理 Mastodon 表情符号 - 转换为 base64 嵌入
        emojis = post.get("emojis", [])
        for emoji in emojis:
            shortcode = emoji.get("shortcode", "")
            url = emoji.get("url", "")
            static_url = emoji.get("static_url", url)
            if shortcode and static_url:
                # 下载 emoji 图片并转换为 base64
                try:
                    emoji_response = requests.get(
                        static_url, timeout=REMOTE_ASSET_TIMEOUT
                    )
                    if emoji_response.status_code == 200:
                        emoji_base64 = base64.b64encode(emoji_response.content).decode(
                            "utf-8"
                        )
                        # 检测图片类型
                        content_type = emoji_response.headers.get(
                            "Content-Type", "image/png"
                        )
                        # 生成 data URI
                        data_uri = f"data:{content_type};base64,{emoji_base64}"
                        # 替换 emoji
                        emoji_pattern = f":{shortcode}:"
                        emoji_img_tag = f'<img src="{data_uri}" alt=":{shortcode}:" class="custom-emoji" title=":{shortcode}:" loading="lazy">'
                        content_html = content_html.replace(
                            emoji_pattern, emoji_img_tag
                        )
                except (requests.RequestException, OSError, ValueError) as e:
                    logging.warning(f"⚠️ 下载 emoji 失败 {shortcode}: {e}")
                    # 失败时使用远程 URL
                    emoji_pattern = f":{shortcode}:"
                    emoji_img_tag = f'<img src="{static_url}" alt=":{shortcode}:" class="custom-emoji" title=":{shortcode}:" loading="lazy">'
                    content_html = content_html.replace(emoji_pattern, emoji_img_tag)

        # 处理时间
        created_at = post["created_at"]
        local_time = get_timezone_aware_datetime(
            created_at, config["sync"]["china_timezone"]
        )

        post_data = {
            "id": post["id"],
            "content": content_html,
            "created_at": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": created_at,  # 使用原始 ISO 格式时间字符串
            "url": post["url"],
            "sensitive": post.get("sensitive", False),
            "spoiler_text": post.get("spoiler_text", ""),
            "visibility": post.get("visibility", "public"),
            "media_attachments": media_items,
            "reblogs_count": post.get("reblogs_count", 0),
            "favourites_count": post.get("favourites_count", 0),
            "replies_count": post.get("replies_count", 0),
            "in_reply_to_id": post.get("in_reply_to_id", None),
            "in_reply_to_account_id": post.get("in_reply_to_account_id", None),
            "account": {
                "id": user_id,
                "username": post["account"]["username"],
                "display_name": post["account"].get(
                    "display_name", post["account"]["username"]
                ),
                "url": post["account"]["url"],
                "avatar": post["account"]["avatar"],
            },
            "tags": [{"name": tag["name"]} for tag in post.get("tags", [])],
        }
        posts_data.append(post_data)

    # 生成 HTML 内容
    html_content = generate_html_template(
        username=username,
        display_name=display_name,
        avatar=avatar,
        instance_name=instance_name,
        background_image=background_image,
        account_url=account_url,
        total_posts=total_posts,
        followers_count=followers_count,
        following_count=following_count,
        posts_data=posts_data,
        user_bio=user_bio,
    )

    # 写入 HTML 文件
    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    logging.info(f"HTML 网页已生成至：{html_filepath}")
    logging.info(f"包含 {total_posts} 条嘟文")
    logging.info(f"图片路径：{media_folder}/")


def get_html_body_template(
    username: str,
    display_name: str,
    avatar: str,
    instance_name: str,
    background_image: str,
    account_url: str,
    total_posts: int,
    followers_count: int,
    following_count: int,
) -> str:
    """生成 HTML body 内容（带用户数据）"""
    escaped_avatar = _escape_text(avatar)
    escaped_display_name = _escape_text(display_name)
    escaped_username = _escape_text(username)
    escaped_instance_name = _escape_text(instance_name)
    escaped_account_url = _escape_text(account_url)

    # 处理背景图片
    bg_style = (
        f" style=\"background-image: url('{_escape_text(background_image)}')\""
        if background_image
        else ""
    )

    return f"""<!-- 图片放大模态框 -->
<div id="imageModal" class="modal">
    <span class="close">&times;</span>
    <img class="modal-content" id="modalImage">
    <div id="caption"></div>
</div>

<header class="header">
    <div class="header-content">
        <div class="search-container">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
            </svg>
            <input type="text" class="search-input" placeholder="搜索嘟文..." id="searchInput" aria-label="搜索嘟文" autocomplete="off" spellcheck="false">
            <button class="clear-btn" id="clearBtn" title="清空搜索" aria-label="清空搜索内容" type="button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                </svg>
            </button>
        </div>
        <button class="theme-toggle" id="themeToggle" title="切换主题"
                aria-label="切换明暗主题" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
        </button>
    </div>
</header>

<main class="container">
    <div class="user-profile">
        <div class="profile-header"{bg_style}></div>
        <div class="profile-info">
            <img src="{escaped_avatar}" alt="{escaped_display_name}" class="user-avatar" onerror="this.style.display='none'">
            <div class="profile-text">
                <h1 class="user-name">
                    <a href="{escaped_account_url}" class="user-name-link" target="_blank">{escaped_display_name}</a>
                </h1>
                <div class="user-handle">@{escaped_username}@{escaped_instance_name}</div>
            </div>
            <div class="user-stats">
                <div class="stat-item">
                    <span class="stat-number">{total_posts}</span>
                    <span class="stat-label">嘟文</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{following_count}</span>
                    <span class="stat-label">关注中</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{followers_count}</span>
                    <span class="stat-label">关注者</span>
                </div>
            </div>
        </div>
    </div>

    <div class="timeline" id="timeline">
        <!-- Posts will be inserted here by JavaScript -->
    </div>

    <div class="pagination" id="pagination">
        <button class="pagination-btn" id="prevBtn" title="上一页"
                aria-label="上一页" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="15 18 9 12 15 6"/>
            </svg>
            上一页
        </button>
        <span class="pagination-info" id="pageInfo" aria-live="polite" aria-atomic="true">第 1 页，共 1 页</span>
        <button class="pagination-btn" id="nextBtn" title="下一页" aria-label="下一页" type="button">
            下一页
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6"/>
            </svg>
        </button>
    </div>

    <div class="no-results" id="noResults" style="display: none;">
        <p>没有找到匹配的嘟文</p>
    </div>
</main>
"""


def generate_html_template(
    username: str,
    display_name: str,
    avatar: str,
    instance_name: str,
    background_image: str,
    account_url: str,
    total_posts: int,
    followers_count: int,
    following_count: int,
    posts_data: List[Dict[str, Any]],
    user_bio: str,
) -> str:
    """生成完整的 HTML 页面"""
    posts_json = _serialize_posts_json(posts_data)
    clean_bio = _escape_text(_strip_html_tags(user_bio)[:160])
    escaped_username = _escape_text(username)
    escaped_instance_name = _escape_text(instance_name)
    escaped_avatar = _escape_text(avatar)

    # 提取的资源
    css_content = load_css_styles()
    js_content = load_javascript()

    # 生成 HTML body（包含用户数据）
    html_body = get_html_body_template(
        username=username,
        display_name=display_name,
        avatar=avatar,
        instance_name=instance_name,
        background_image=background_image,
        account_url=account_url,
        total_posts=total_posts,
        followers_count=followers_count,
        following_count=following_count,
    )

    # 组装完整 HTML
    html_output = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{escaped_username}的 Mastodon 备份</title>
    <meta name="description" content="{clean_bio}">
    <meta property="og:title" content="@{escaped_username}@{escaped_instance_name}">
    <meta property="og:description" content="{clean_bio}">
    <meta property="og:type" content="profile">
    <link rel="icon" type="image/png" href="{escaped_avatar}">
    <style>
{css_content}
    </style>
</head>
<body>
{html_body}
    <script id="posts-data" type="application/json">{posts_json}</script>
    <script>
        const postsData = JSON.parse(document.getElementById("posts-data").textContent);

{js_content}
    </script>
</body>
</html>"""
    return html_output
