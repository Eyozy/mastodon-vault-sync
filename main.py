# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
import re
import shutil
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

import requests
import yaml
from markdownify import markdownify as md

# --- 配置日志记录 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# --- 辅助函数 ---

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
                "check_edit_limit": int(os.environ.get("CHECK_EDIT_LIMIT") or 40),
            },
            "sync": {"state_file": "sync_state.json"}
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
        backup_conf.setdefault("check_edit_limit", 40)
        return config
    except FileNotFoundError:
        logging.error("❌ 错误：找不到 config.yaml 文件。程序无法运行。")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"❌ 错误：配置文件格式错误：{e}")
        sys.exit(1)

def fetch_mastodon_posts(config, since_id=None, page_limit=None):
    mastodon_config = config["mastodon"]
    instance_url, user_id, access_token = mastodon_config["instance_url"], mastodon_config["user_id"], mastodon_config["access_token"]
    api_url = f"{instance_url}/api/v1/accounts/{user_id}/statuses"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 40, "exclude_replies": False, "exclude_reblogs": True}
    if since_id: params["since_id"] = since_id
    all_posts, page_count = [], 1
    while api_url:
        try:
            logging.info(f"📄 正在获取第 {page_count} 页...")
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            posts = response.json()
            if not posts: break
            all_posts.extend(posts)
            if page_limit and page_count >= page_limit: break
            links = requests.utils.parse_header_links(response.headers.get('Link', ''))
            api_url = next((link['url'] for link in links if link.get('rel') == 'next'), None)
            params.pop('since_id', None)
            page_count += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ API 请求失败：{e}")
            return []
    all_posts.reverse()
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

def format_single_post_for_archive(post, media_folder_name, media_file_map):
    cst_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    time_str = cst_dt.strftime("%H:%M")
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

def format_post_for_single_file(post, media_folder_name, media_file_map):
    cst_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    frontmatter = {
        "id": post["id"], "createdAt": cst_dt.strftime("%Y-%m-%d %H:%M:%S"),
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
        existing_posts_by_id[post['id']] = format_single_post_for_archive(post, media_folder_name, config["media_file_map"]).strip()
    if not config.get("is_full_sync", False):
        deleted_ids = set(existing_posts_by_id.keys()) - {p['id'] for p in all_posts_from_server}
        if deleted_ids:
            logging.info(f"🗑️ 检测到 {len(deleted_ids)} 条已删除的帖子，将从归档中移除。")
            for post_id in deleted_ids: del existing_posts_by_id[post_id]
    rebuilt_posts_by_day = defaultdict(list)
    all_posts_dict = {p['id']: p for p in all_posts_from_server}
    for post_id, content in existing_posts_by_id.items():
        if (post_data := all_posts_dict.get(post_id)):
            cst_dt = datetime.strptime(post_data["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
            rebuilt_posts_by_day[cst_dt.strftime("%Y-%m-%d")].append({'content': content, 'created_at': post_data['created_at']})
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
        cst_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
        filename = f"{cst_dt.strftime('%Y-%m-%d_%H%M%S')}_{post['id']}.md"
        file_path = posts_folder_path / filename
        new_content = format_post_for_single_file(post, backup_config["media_folder"], media_file_map)
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

def main():
    logging.info("========================================")
    logging.info(" Mastodon Sync 开始运行")
    logging.info("========================================")
    config = get_config()

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
    is_automatic_full_sync = not archive_file_path.exists()
    is_full_sync = is_cli_full_sync or is_action_full_sync or is_automatic_full_sync
    config["is_full_sync"] = is_full_sync

    if is_full_sync:
        logging.warning("⚠️  检测到全量同步模式，将清理目标路径下的旧备份文件...")
        # 状态文件在项目目录，也要清理
        if state_file_path.exists(): state_file_path.unlink()
        if archive_file_path.exists(): archive_file_path.unlink()
        if posts_folder_path.exists(): shutil.rmtree(posts_folder_path)
        if media_folder_path.exists(): shutil.rmtree(media_folder_path)
    
    last_synced_id = None
    if not is_full_sync and state_file_path.exists():
        try:
            last_synced_id = json.loads(state_file_path.read_text())['last_synced_id']
        except (json.JSONDecodeError, KeyError):
            logging.warning("⚠️ 同步状态文件格式不正确，将执行全量同步。")
            is_full_sync = True
            config["is_full_sync"] = True

    if is_full_sync:
        posts_to_process = fetch_mastodon_posts(config)
        all_posts_from_server_for_sync = posts_to_process
    else:
        new_posts = fetch_mastodon_posts(config, since_id=last_synced_id)
        num_pages = (backup_config["check_edit_limit"] + 39) // 40
        recent_posts = fetch_mastodon_posts(config, page_limit=num_pages)
        all_posts_from_server_for_sync = recent_posts
        posts_dict = {p['id']: p for p in new_posts}
        for p in recent_posts: posts_dict[p['id']] = p
        posts_to_process = sorted(list(posts_dict.values()), key=lambda p: p['created_at'])

    if posts_to_process:
        save_posts(posts_to_process, config, all_posts_from_server_for_sync, backup_path)
        all_ids = [p['id'] for p in posts_to_process]
        if last_synced_id and not is_full_sync: all_ids.append(last_synced_id)
        if all_ids: 
            state_file_path.write_text(json.dumps({"last_synced_id": max(all_ids, key=int)}))
    else:
        logging.info("✨ 没有新内容需要同步。")
        
    # 无论是否有新内容，只要在全量同步模式或首次运行，就生成活动总结
    if is_full_sync or not archive_file_path.exists():
        logging.info("🔄 全量同步模式或首次运行，生成活动总结...")
        generate_activity_summary(config, backup_path)
    else:
        # 检查是否需要更新活动总结（例如日期变化）
        summary_filepath = backup_path / backup_config["summary_filename"]
        if not summary_filepath.exists():
            logging.info("📊 活动总结文件不存在，生成新的...")
            generate_activity_summary(config, backup_path)
        else:
            logging.info("📊 活动总结已存在，跳过生成。")
    logging.info("========================================")
    logging.info(" ✅ 同步完成！")
    logging.info("========================================")

if __name__ == "__main__":
    main()
