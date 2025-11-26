# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import re
import shutil
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

import requests
import yaml
import base64
from markdownify import markdownify as md
import template  # HTML 模板模块

# --- API 请求配置常量 ---
POSTS_PER_REQUEST = 40      # 每次请求的最大帖子数量 (Mastodon API 限制)
RATE_LIMIT_THRESHOLD = 10   # 速率限制安全阈值，低于此值时触发等待
DEFAULT_WAIT_TIME = 300     # 默认等待时间（秒），当无法解析速率限制重置时间时使用

# --- 配置日志记录 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# --- 辅助函数 ---

def load_css_styles():
    """
    从外部文件加载 CSS 样式
    """
    try:
        # 尝试从本地文件读取
        css_file = Path("styles/mastodon.css")
        if css_file.exists():
            with open(css_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logging.warning("CSS 文件不存在，使用默认样式")
            return get_default_css()
    except Exception as e:
        logging.error(f"读取 CSS 文件失败：{e}，使用默认样式")
        return get_default_css()

def get_default_css():
    """
    返回默认的内联 CSS（作为后备）
    """
    return """
    /* 基础样式后备方案 */
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .container { max-width: 600px; margin: 0 auto; }
    .status { background: white; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
    """

def validate_post_data(post_data):
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

    except Exception as e:
        logging.warning(f"帖子数据验证失败：{e}")
        return False

def validate_config(config):
    """
    验证配置的安全性和完整性
    """
    try:
        # 验证 Mastodon 配置
        mastodon_config = config["mastodon"]

        # 检查必需字段
        required_fields = ["instance_url", "user_id", "access_token"]
        for field in required_fields:
            if not mastodon_config.get(field):
                raise ValueError(f"配置错误：缺少必需的 Mastodon 配置字段：{field}")

        # 验证 URL 格式
        instance_url = mastodon_config["instance_url"]
        if not instance_url.startswith(("http://", "https://")):
            raise ValueError("配置错误：instance_url 必须以 http:// 或 https:// 开头")

        # 验证 user_id 是否为数字
        try:
            int(mastodon_config["user_id"])
        except ValueError:
            raise ValueError("配置错误：user_id 必须是数字")

        # 验证 access_token 长度
        if len(mastodon_config["access_token"]) < 10:
            raise ValueError("配置错误：access_token 长度不足")

        logging.info("✔ 配置验证通过")
        return True

    except KeyError as e:
        raise ValueError(f"配置错误：缺少配置项 {e}")
    except Exception as e:
        logging.error(f"❌ 配置验证失败：{e}")
        raise

def get_config():
    """
    根据运行环境（GitHub Actions 或本地）加载配置。
    """
    # 如果在 GitHub Actions 环境中
    if os.environ.get("GITHUB_ACTIONS") == "true":
        logging.info("✔ 检测到 GitHub Actions 环境，使用环境变量配置。")
        return {
            "mastodon": {
                "instance_url": os.environ.get("MASTODON_INSTANCE_URL"),
                "user_id": os.environ.get("MASTODON_USER_ID"),
                "access_token": os.environ.get("MASTODON_ACCESS_TOKEN"),
            },
            "backup": {
                "path": ".", # 在 Actions 中，路径就是仓库根目录
                "filename": os.environ.get("ARCHIVE_FILENAME") or "archive.md",
                "posts_folder": os.environ.get("POSTS_FOLDER") or "mastodon",
                "media_folder": os.environ.get("MEDIA_FOLDER") or "media",
                "summary_filename": os.environ.get("SUMMARY_FILENAME") or "README.md",
                "html_filename": os.environ.get("HTML_FILENAME") or "index.html",
            },
            "sync": {
                "state_file": "sync_state.json",
                "china_timezone": os.environ.get("CHINA_TIMEZONE", "false").lower() == "true"
            }
        }

    # 如果是本地运行，则从 config.yaml 加载
    logging.info("✔ 本地运行模式，尝试从 config.yaml 文件加载。")
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.info("✔ 配置文件加载成功。")
        # 确保 backup 部分存在并提供默认值
        backup_conf = config.setdefault("backup", {})
        backup_conf.setdefault("path", ".")
        backup_conf.setdefault("posts_folder", "mastodon")
        backup_conf.setdefault("filename", "archive.md")
        backup_conf.setdefault("media_folder", "media")
        backup_conf.setdefault("summary_filename", "README.md")

        # 确保 sync 部分存在并提供默认值
        sync_conf = config.setdefault("sync", {})
        sync_conf.setdefault("china_timezone", False)

        return config
    except FileNotFoundError:
        logging.error("❌ 错误：找不到 config.yaml 文件。程序无法运行。")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"❌ 错误：配置文件格式错误：{e}")
        sys.exit(1)

def get_timezone_aware_datetime(created_at_str, china_timezone=False):
    """
    根据配置的时区设置转换时间字符串

    Args:
        created_at_str: ISO 格式的时间字符串
        china_timezone: 是否使用中国时区（GMT+8）

    Returns:
        转换后的带时区的 datetime 对象
    """
    dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

    if china_timezone:
        # 使用中国时区 (GMT+8)
        return dt.astimezone(timezone(timedelta(hours=8)))
    else:
        # 使用 UTC
        return dt

def parse_rate_limit_reset(reset_header):
    """解析 Mastodon API 的 X-RateLimit-Reset 时间戳"""
    try:
        # 尝试解析为 Unix 时间戳（秒数）
        return int(reset_header)
    except ValueError:
        pass  # 继续尝试其他格式

    try:
        # 尝试解析为 ISO 格式时间戳
        if 'T' in reset_header:
            # 移除微秒部分，避免解析问题
            clean_time = reset_header.split('.')[0] + ('Z' if reset_header.endswith('Z') else '')
            if reset_header.endswith('Z'):
                reset_time = datetime.strptime(clean_time, "%Y-%m-%dT%H:%M:%SZ")
                reset_time = reset_time.replace(tzinfo=timezone.utc)
            else:
                reset_time = datetime.fromisoformat(clean_time)
            return int(reset_time.timestamp())
    except (ValueError, AttributeError):
        pass

    # 如果都失败了，返回 None，使用默认值
    return None

def fetch_mastodon_posts(config, since_id=None, page_limit=None, max_posts=None):
    mastodon_config = config["mastodon"]
    instance_url, user_id, access_token = mastodon_config["instance_url"], mastodon_config["user_id"], mastodon_config["access_token"]
    api_url = f"{instance_url}/api/v1/accounts/{user_id}/statuses"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": POSTS_PER_REQUEST, "exclude_replies": False, "exclude_reblogs": True}
    if since_id: params["since_id"] = since_id
    all_posts, page_count = [], 1
    requests_in_window = 0
    window_start_time = time.time()

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
                    # 实时倒计时显示
                    total_wait = int(wait_time)
                    for remaining in range(total_wait, 0, -1):
                        progress = "█" * ((total_wait - remaining) * 20 // total_wait)
                        empty = "░" * (20 - len(progress))
                        # 使用 \r 回到行首，实现倒计时效果
                        print(f"\r⏳ 等待重置：[{progress}{empty}] {remaining:3d}s ({(total_wait-remaining)*100//total_wait}%)  ", end="", flush=True)
                        time.sleep(1)
                    print()  # 换行
                    logging.info("✅ API 限制已重置，继续获取帖子...")
                    requests_in_window = 0
                    window_start_time = time.time()

            # 每获取 100 页显示一次进度报告
            if page_count % 100 == 0 or page_count % 25 == 1:
                logging.info(f"📊 进度报告：已获取 {len(all_posts)} 条帖子，共 {page_count} 页")
            logging.info(f"📄 正在获取第 {page_count} 页...（当前窗口已调用 {requests_in_window}/300 次）")
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()

            # 检查 API 返回的速率限制头
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))

            # 解析 X-RateLimit-Reset 时间戳
            reset_header = response.headers.get('X-RateLimit-Reset', '0')
            rate_limit_reset = parse_rate_limit_reset(reset_header)

            # 如果解析失败，使用默认值（当前时间 + 默认等待时间）
            if rate_limit_reset is None:
                rate_limit_reset = int(time.time()) + DEFAULT_WAIT_TIME
                logging.warning(f"⚠️ 无法解析 API 重置时间格式：{reset_header}，使用默认等待时间")

            posts = response.json()
            if not posts: break
            all_posts.extend(posts)
            requests_in_window += 1

            # 检查是否达到限制
            if page_limit and page_count >= page_limit: break
            if max_posts and len(all_posts) >= max_posts:
                all_posts = all_posts[:max_posts]
                break

            # 如果剩余调用次数很少，等待重置
            if rate_limit_remaining < RATE_LIMIT_THRESHOLD:
                reset_wait = max(0, rate_limit_reset - current_time)
                if reset_wait > 0 and reset_wait < 300:  # 不超过 5 分钟
                    logging.info(f"⏱️ API 调用即将用完，等待 {reset_wait:.1f} 秒重置...")
                    # 实时倒计时显示
                    total_wait = int(reset_wait)
                    for remaining in range(total_wait, 0, -1):
                        progress = "█" * ((total_wait - remaining) * 20 // total_wait)
                        empty = "░" * (20 - len(progress))
                        print(f"\r⏳ API 重置：[{progress}{empty}] {remaining:3d}s ({(total_wait-remaining)*100//total_wait}%)  ", end="", flush=True)
                        time.sleep(1)
                    print()  # 换行
                    logging.info("✅ API 限制已重置，继续获取帖子...")
                    requests_in_window = 0

            links = requests.utils.parse_header_links(response.headers.get('Link', ''))
            api_url = next((link['url'] for link in links if link.get('rel') == 'next'), None)
            params.pop('since_id', None)
            page_count += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ API 请求失败：{e}")
            return []

    all_posts.reverse()
    logging.info(f"✅ 成功获取 {len(all_posts)} 条帖子，共调用 {page_count-1} 次 API")
    return all_posts

def download_media(media_item, media_folder_path):
    try:
        original_filename = Path(urlparse(media_item['url']).path).name
        local_filename = f"{media_item['id']}-{original_filename}"
        local_file_path = media_folder_path / local_filename
        if not local_file_path.exists():
            logging.info(f"⬇️  正在下载媒体文件：{media_item['url']}")
            response = requests.get(media_item['url'], stream=True)
            response.raise_for_status()
            with open(local_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        return local_filename
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 下载媒体文件失败：{media_item['url']} - {e}")
        return None

def format_single_post_for_archive(post, media_folder_name, media_file_map, china_timezone=False):
    local_dt = get_timezone_aware_datetime(post["created_at"], china_timezone)
    time_str = local_dt.strftime("%H:%M")
    is_reply = post.get("in_reply_to_id")
    icon = "💬" if is_reply else "📝"
    heading = f"## {time_str} {icon} {'回复' if is_reply else '嘟文'}"
    source_link_text = "**回复嘟文**" if is_reply else "**原始嘟文**"
    content_md = md(post["content"], heading_style="ATX").strip()
    attachments_md = ""
    if post["media_attachments"]:
        media_parts = []
        for media in post["media_attachments"]:
            if (local_filename := media_file_map.get(media['id'])):
                media_path = f"{media_folder_name}/{local_filename}"
                media_parts.append(f"![{media.get('description') or 'Image'}]({media_path})")
        if media_parts:
            attachments_md = ("\n\n" if content_md else "") + "\n".join(media_parts)
    return f"{heading}\n\n**内容**：{content_md}{attachments_md}\n\n{source_link_text}：{post['url']}\n\n---\n\n"

def format_post_for_single_file(post, media_folder_name, media_file_map, china_timezone=False):
    local_dt = get_timezone_aware_datetime(post["created_at"], china_timezone)
    frontmatter = {
        "id": post["id"], "createdAt": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "source": post["url"], "type": "reply" if post["in_reply_to_id"] else "toot",
        "tags": [f"#{tag['name']}" for tag in post["tags"]]}
    if post["in_reply_to_id"]:
        frontmatter.update({"inReplyToId": post["in_reply_to_id"], "inReplyToAccountId": post["in_reply_to_account_id"]})
    yaml_frontmatter = "---\n" + yaml.dump(frontmatter, allow_unicode=True) + "---\n\n"
    content_md = md(post["content"], heading_style="ATX")
    attachments_md = ""
    if post["media_attachments"]:
        media_parts = []
        for media in post["media_attachments"]:
            if (local_filename := media_file_map.get(media['id'])):
                media_path = f"../{media_folder_name}/{local_filename}"
                media_parts.append(f"![{media.get('description') or 'Image'}]({media_path})\n")
        if media_parts: attachments_md = "\n## 附件\n" + "".join(media_parts)
    return yaml_frontmatter + content_md + attachments_md

def update_archive_file(posts_to_update, config, all_posts_from_server, backup_path):
    backup_config = config["backup"]
    media_folder_name, archive_filename = backup_config["media_folder"], backup_config["filename"]
    archive_file_path = backup_path / archive_filename
    existing_posts_by_id = {}
    if archive_file_path.exists():
        with open(archive_file_path, 'r', encoding='utf-8') as f: content = f.read()
        for block in content.split('---\n'):
            if block.strip() and (match := re.search(r'https://[^\/]+\/[^\/]+\/(\d+)', block)):
                existing_posts_by_id[match.group(1)] = block
    for post in posts_to_update:
        existing_posts_by_id[post['id']] = format_single_post_for_archive(post, media_folder_name, config["media_file_map"], config["sync"]["china_timezone"]).strip()
    # 编辑检测范围：最近 200 条帖子（约 1-2 周的内容）
    logging.info("📝 编辑检测范围：最近 200 条帖子，覆盖约 1-2 周内的编辑更新")
    rebuilt_posts_by_day = defaultdict(list)
    all_posts_dict = {p['id']: p for p in all_posts_from_server}
    for post_id, content in existing_posts_by_id.items():
        if (post_data := all_posts_dict.get(post_id)):
            local_dt = get_timezone_aware_datetime(post_data["created_at"], config["sync"]["china_timezone"])
            rebuilt_posts_by_day[local_dt.strftime("%Y-%m-%d")].append({'content': content, 'created_at': post_data['created_at']})
    final_content = ""
    for date_str in sorted(rebuilt_posts_by_day.keys(), reverse=True):
        final_content += f"# {date_str}\n\n"
        day_posts = sorted(rebuilt_posts_by_day[date_str], key=lambda p: p['created_at'], reverse=True)
        final_content += '\n'.join([p['content'] for p in day_posts]) + '\n\n'
    with open(archive_file_path, 'w', encoding='utf-8') as f: f.write(final_content)
    logging.info(f"✍️  已更新归档文件：{archive_file_path}")

def save_posts(posts, config, all_posts_from_server, backup_path):
    backup_config = config["backup"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]
    media_file_map = {}
    for post in posts:
        if post.get("media_attachments"):
            media_folder_path.mkdir(parents=True, exist_ok=True)
            for media in post["media_attachments"]:
                if (local_filename := download_media(media, media_folder_path)):
                    media_file_map[media['id']] = local_filename
    config["media_file_map"] = media_file_map
    update_archive_file(posts, config, all_posts_from_server, backup_path)
    posts_folder_path.mkdir(parents=True, exist_ok=True)
    for post in posts:
        local_dt = get_timezone_aware_datetime(post["created_at"], config["sync"]["china_timezone"])
        filename = f"{local_dt.strftime('%Y-%m-%d_%H%M%S')}_{post['id']}.md"
        file_path = posts_folder_path / filename
        new_content = format_post_for_single_file(post, backup_config["media_folder"], media_file_map, config["sync"]["china_timezone"])
        if not file_path.exists() or file_path.read_text('utf-8') != new_content:
            try:
                file_path.write_text(new_content, encoding='utf-8')
                logging.info(f"📄 已备份/更新单条嘟文：{file_path}")
            except IOError as e:
                logging.error(f"❌ 无法写入文件 {file_path}: {e}")

def get_color_from_count(count):
    if count == 0: return "#ebedf0"
    if 1 <= count <= 2: return "#9be9a8"
    if 3 <= count <= 5: return "#40c463"
    if 6 <= count <= 9: return "#30a14e"
    return "#216e39"

def generate_heatmap_svg(post_counts, year, output_path):
    logging.info(f"🎨 正在为 {year} 年生成 SVG 热力图...")
    SQUARE_SIZE, SPACING = 10, 3; SQUARE_TOTAL_SIZE = SQUARE_SIZE + SPACING
    X_OFFSET, Y_OFFSET = 25, 20; WIDTH = X_OFFSET + SQUARE_TOTAL_SIZE * 53 + SPACING; HEIGHT = Y_OFFSET + SQUARE_TOTAL_SIZE * 7
    svg_parts = [f'<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">', '<style>.month-label, .wday-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"; font-size: 9px; fill: #767676; }</style>']
    for day, label in {1: "M", 3: "W", 5: "F"}.items():
        svg_parts.append(f'<text x="0" y="{Y_OFFSET + day * SQUARE_TOTAL_SIZE + SQUARE_SIZE}" class="wday-label">{label}</text>')
    year_start, month_labels = date(year, 1, 1), {}
    year_start_weekday = (year_start.weekday() + 1) % 7
    days_in_year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    for day_of_year in range(days_in_year):
        current_date = year_start + timedelta(days=day_of_year)
        if current_date.year != year: continue
        if current_date.day == 1 and day_of_year > 0:
            month_labels[(day_of_year + year_start_weekday) // 7] = current_date.strftime("%b")
        count = post_counts.get(current_date, 0)
        total_days = day_of_year + year_start_weekday
        x_pos, y_pos = X_OFFSET + (total_days // 7) * SQUARE_TOTAL_SIZE, Y_OFFSET + (total_days % 7) * SQUARE_TOTAL_SIZE
        tooltip = f"{current_date.strftime('%Y-%m-%d')}: {count} post{'s' if count != 1 else ''}"
        svg_parts.append(f'<rect x="{x_pos}" y="{y_pos}" width="{SQUARE_SIZE}" height="{SQUARE_SIZE}" fill="{get_color_from_count(count)}" rx="2" ry="2"><title>{tooltip}</title></rect>')
    for week, month in month_labels.items():
        svg_parts.append(f'<text x="{X_OFFSET + week * SQUARE_TOTAL_SIZE}" y="{Y_OFFSET - 8}" class="month-label">{month}</text>')
    svg_parts.append("</svg>")
    with open(output_path, 'w', encoding='utf-8') as f: f.write("\n".join(svg_parts))
    logging.info(f"✅ 热力图已成功生成至 '{output_path.name}'。")

def generate_activity_summary(config, backup_path):
    logging.info("📊 正在生成活动总结报告...")
    backup_config = config["backup"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    summary_filepath = backup_path / backup_config["summary_filename"]
    heatmap_svg_filename = "heatmap.svg"
    heatmap_svg_filepath = backup_path / heatmap_svg_filename

    if not posts_folder_path.exists() or not any(posts_folder_path.iterdir()):
        logging.warning("⚠️ 未找到帖子备份文件夹或文件夹为空，无法生成总结报告。")
        return

    all_posts = []
    for post_file in sorted(list(posts_folder_path.glob("*.md")), reverse=True):
        try:
            with open(post_file, 'r', encoding='utf-8') as f: content = f.read()
            parts = content.split('---', 2)
            if len(parts) < 3: continue
            frontmatter = yaml.safe_load(parts[1])
            all_posts.append({
                "datetime": datetime.strptime(frontmatter["createdAt"], "%Y-%m-%d %H:%M:%S"),
                "content": parts[2].strip().replace('../media/', './media/'),
                "source": frontmatter.get("source", ""), "type": frontmatter.get("type", "toot")
            })
        except Exception as e:
            logging.error(f"❌ 处理文件 {post_file.name} 时出错：{e}")
    
    if not all_posts:
        summary_filepath.write_text("# Mastodon 活动总结\n\n未找到任何帖子来生成报告。", encoding='utf-8')
        return

    today = date.today()
    current_year = today.year
    post_counts = defaultdict(int)
    for post in all_posts:
        if post["datetime"].year == current_year: post_counts[post["datetime"].date()] += 1
    
    generate_heatmap_svg(post_counts, current_year, heatmap_svg_filepath)
    total_posts_this_year = sum(post_counts.values())

    # 注意：最近嘟文代码已删除，因为活动总结不再包含这部分内容

    final_md = (f"# Mastodon 活动总结\n\n截至 {today.strftime('%Y-%m-%d')} 的活动概览。\n\n"
                f"## {current_year} 年活动热力图\n\n今年以来，你一共发布了 {total_posts_this_year} 篇嘟文。\n\n"
                f"![Activity Heatmap](./{heatmap_svg_filename})")
    summary_filepath.write_text(final_md, encoding='utf-8')
    logging.info(f"✅ 活动总结报告已成功更新至 '{summary_filepath.name}'。")

def generate_mastodon_html(posts, config, backup_path):
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
        instance_name = user_url.split("//")[1].split("/")[0] if "//" in user_url else ""
        # 获取用户背景图片
        header = user.get("header", "")
        if header:
            header_filename = f"header-{user_id}.jpg"
            local_header_path = f"{media_folder}/{header_filename}"

            # 下载背景图片
            try:
                header_response = requests.get(header, stream=True)
                if header_response.status_code == 200:
                    header_path = backup_path / media_folder / header_filename
                    header_path.parent.mkdir(exist_ok=True)
                    with open(header_path, 'wb') as f:
                        for chunk in header_response.iter_content(1024):
                            f.write(chunk)
                    background_image = local_header_path
                else:
                    background_image = ""
            except Exception as e:
                logging.warning(f"下载背景图片失败：{e}")
                background_image = ""
        else:
            background_image = ""
    else:
        username = "unknown"
        display_name = "Unknown User"
        avatar = ""
        user_id = "unknown"
        instance_name = ""
        background_image = ""

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
            media_items.append({
                "id": media["id"],
                "type": media["type"],
                "url": f"{media_folder}/{media_filename}",
                "description": media.get("description", ""),
                "preview_url": media.get("preview_url", "")
            })

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
                    emoji_response = requests.get(static_url, timeout=10)
                    if emoji_response.status_code == 200:
                        emoji_base64 = base64.b64encode(emoji_response.content).decode('utf-8')
                        # 检测图片类型
                        content_type = emoji_response.headers.get('Content-Type', 'image/png')
                        # 生成 data URI
                        data_uri = f"data:{content_type};base64,{emoji_base64}"
                        # 替换 emoji
                        emoji_pattern = f":{shortcode}:"
                        emoji_img_tag = f'<img src="{data_uri}" alt=":{shortcode}:" class="custom-emoji" title=":{shortcode}:" loading="lazy">'
                        content_html = content_html.replace(emoji_pattern, emoji_img_tag)
                except Exception as e:
                    logging.warning(f"⚠️ 下载 emoji 失败 {shortcode}: {e}")
                    # 失败时使用远程 URL
                    emoji_pattern = f":{shortcode}:"
                    emoji_img_tag = f'<img src="{static_url}" alt=":{shortcode}:" class="custom-emoji" title=":{shortcode}:" loading="lazy">'
                    content_html = content_html.replace(emoji_pattern, emoji_img_tag)

        # 处理时间
        created_at = post["created_at"]
        local_time = get_timezone_aware_datetime(created_at, config["sync"]["china_timezone"])

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
                "display_name": post["account"].get("display_name", post["account"]["username"]),
                "url": post["account"]["url"],
                "avatar": post["account"]["avatar"]
            },
            "tags": [{"name": tag["name"]} for tag in post.get("tags", [])]
        }
        posts_data.append(post_data)

    # 生成 HTML 内容
    html_content = generate_html_template(username, display_name, avatar, instance_name, background_image,
                                        total_posts, followers_count, following_count,
                                        posts_data)

    # 写入 HTML 文件
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logging.info(f"HTML 网页已生成至：{html_filepath}")
    logging.info(f"包含 {total_posts} 条嘟文")
    logging.info(f"图片路径：{media_folder}/")

def generate_html_template(username, display_name, avatar, instance_name, background_image,
                          total_posts, followers_count, following_count,
                          posts_data):
    """生成完整的 HTML 页面"""

    # 将 posts_data 转换为 JSON 字符串
    posts_json = json.dumps(posts_data, ensure_ascii=False)

    # 使用 template.py 生成 HTML
    return template.generate_html(
        username=username,
        display_name=display_name,
        avatar=avatar,
        instance_name=instance_name,
        background_image=background_image,
        total_posts=total_posts,
        followers_count=followers_count,
        following_count=following_count,
        posts_json=posts_json
    )


def safe_remove_directory(path):
    """
    安全删除目录，处理权限问题和文件锁定
    """
    if not path.exists():
        return True
    
    try:
        # 首先尝试正常删除
        shutil.rmtree(path)
        return True
    except PermissionError as e:
        logging.warning(f"⚠️ 权限错误，尝试强制删除目录 {path}: {e}")
        
        # 尝试移除只读属性
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.chmod(file_path, 0o777)
                    except (OSError, PermissionError):
                        pass
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        os.chmod(dir_path, 0o777)
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            logging.warning(f"⚠️ 移除只读属性失败：{e}")
        
        # 再次尝试删除
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            # 如果还是失败，尝试逐个删除文件
            try:
                import stat
                def remove_readonly(func, path, excinfo):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                
                shutil.rmtree(path, onerror=remove_readonly)
                return True
            except Exception as e:
                logging.error(f"❌ 无法删除目录 {path}: {e}")
                return False
    except Exception as e:
        logging.error(f"❌ 删除目录 {path} 时发生未知错误：{e}")
        return False

def safe_remove_file(path):
    """
    安全删除文件，处理权限问题
    """
    if not path.exists():
        return True
    
    try:
        path.unlink()
        return True
    except PermissionError as e:
        logging.warning(f"⚠️ 权限错误，尝试强制删除文件 {path}: {e}")
        try:
            # 尝试移除只读属性
            os.chmod(path, 0o777)
            path.unlink()
            return True
        except Exception as e:
            logging.error(f"❌ 无法删除文件 {path}: {e}")
            return False
    except Exception as e:
        logging.error(f"❌ 删除文件 {path} 时发生未知错误：{e}")
        return False

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

def main():
    logging.info("========================================")
    logging.info(" Mastodon Sync 开始运行")
    logging.info("========================================")
    config = get_config()

    # 验证配置
    try:
        validate_config(config)
    except ValueError as e:
        logging.error(f"配置验证失败：{e}")
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

    is_cli_full_sync = "--full-sync" in sys.argv
    is_action_full_sync = os.environ.get("FORCE_FULL_SYNC") == "true"
    is_first_run = not archive_file_path.exists()
    is_manual_full_sync = is_cli_full_sync or is_action_full_sync
    is_full_sync = is_manual_full_sync or is_first_run
    config["is_full_sync"] = is_full_sync

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
            logging.error("❌ 建议：关闭可能占用文件夹的程序（如文件浏览器、OneDrive 同步等）后重试")
            # 选择性退出，因为无法删除文件夹可能会导致后续操作失败
            if posts_folder_path.exists():
                logging.error("❌ 由于无法清理旧文件，为了安全起见，程序将退出")
                sys.exit(1)
        
        if not safe_remove_directory(media_folder_path):
            logging.error("❌ 无法删除媒体文件夹，但继续执行...")
    
    last_synced_id = None
    if not is_full_sync and state_file_path.exists():
        try:
            last_synced_id = json.loads(state_file_path.read_text())['last_synced_id']
        except (json.JSONDecodeError, KeyError):
            logging.warning("⚠️ 同步状态文件格式不正确，将执行全量同步。")
            is_full_sync = True
            config["is_full_sync"] = True

    if is_full_sync:
        # 智能全量同步：充分利用 API 限制获取所有帖子
        # 无页数限制，通过智能速率管理安全获取所有历史帖子
        logging.info("🔄 智能全量同步模式，将获取所有历史帖子...")
        logging.info("⚡ 系统将智能管理 API 速率限制，可能需要一些时间完成")
        posts_to_process = fetch_mastodon_posts(config)
        all_posts_from_server_for_sync = posts_to_process
        new_posts_count = len(posts_to_process)
        logging.info(f"📊 全量同步完成，共获取 {new_posts_count} 条历史帖子")
    else:
        new_posts = fetch_mastodon_posts(config, since_id=last_synced_id)
        # 获取更多帖子用于编辑检测（5 页，200 条帖子），覆盖过去 1-2 周的编辑
        recent_posts = fetch_mastodon_posts(config, page_limit=5)
        all_posts_from_server_for_sync = recent_posts
        posts_dict = {p['id']: p for p in new_posts}
        for p in recent_posts: posts_dict[p['id']] = p
        posts_to_process = sorted(list(posts_dict.values()), key=lambda p: p['created_at'])
        new_posts_count = len(new_posts)

    if posts_to_process:
        save_posts(posts_to_process, config, all_posts_from_server_for_sync, backup_path)
        all_ids = [p['id'] for p in posts_to_process]
        if last_synced_id and not is_full_sync: all_ids.append(last_synced_id)
        if all_ids: 
            state_file_path.write_text(json.dumps({"last_synced_id": max(all_ids, key=int)}))
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
                all_posts_for_html = fetch_mastodon_posts(config)
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

    logging.info("========================================")
    logging.info("同步完成！")
    logging.info("========================================")

if __name__ == "__main__":
    # 运行主程序
    main()
