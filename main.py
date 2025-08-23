# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
import re
import shutil
from datetime import datetime, timezone, timedelta
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
    优先从环境变量获取配置，如果找不到则回退到 config.yaml 文件。
    这是为了适配 GitHub Actions 的安全实践。
    """
    config = {}
    
    # 尝试从环境变量加载
    mastodon_instance_url = os.environ.get("MASTODON_INSTANCE_URL")
    mastodon_user_id = os.environ.get("MASTODON_USER_ID")
    mastodon_access_token = os.environ.get("MASTODON_ACCESS_TOKEN")
    
    # 健壮地获取配置，处理空字符串的情况
    archive_filename = os.environ.get("ARCHIVE_FILENAME") or "archive.md"
    posts_folder = os.environ.get("POSTS_FOLDER") or "mastodon"
    media_folder = os.environ.get("MEDIA_FOLDER") or "media"
    check_edit_limit = int(os.environ.get("CHECK_EDIT_LIMIT") or 40)

    if mastodon_instance_url and mastodon_user_id and mastodon_access_token:
        logging.info("✔ 使用环境变量中的配置。")
        config = {
            "mastodon": {
                "instance_url": mastodon_instance_url,
                "user_id": mastodon_user_id,
                "access_token": mastodon_access_token,
            },
            "backup": {
                "path": ".", # 在 Actions 环境中，路径是相对于仓库根目录的
                "archive_filename": archive_filename,
                "posts_folder": posts_folder,
                "media_folder": media_folder,
                "check_edit_limit": check_edit_limit,
            },
            "sync": {"state_file": "sync_state.json"}
        }
        return config

    # 如果环境变量不完整，则尝试加载本地配置文件
    logging.warning("⚠️ 未找到完整的环境变量配置，将尝试从 config.yaml 文件加载。")
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.info("✔ 配置文件加载成功。")
        # 为本地配置添加默认值（如果不存在）
        backup_conf = config.setdefault("backup", {})
        backup_conf.setdefault("archive_filename", "archive.md")
        backup_conf.setdefault("posts_folder", "mastodon")
        backup_conf.setdefault("media_folder", "media")
        backup_conf.setdefault("check_edit_limit", 40)
        return config
    except FileNotFoundError:
        logging.error("❌ 错误：既未找到环境变量配置，也找不到 config.yaml 文件。程序无法运行。")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"❌ 错误：配置文件格式错误：{e}")
        sys.exit(1)

def load_sync_state(state_file_path):
    """加载上次同步的状态"""
    if not state_file_path.exists():
        logging.warning("ℹ 未找到同步状态文件，将从头开始同步。")
        return None
    try:
        with open(state_file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
            return state.get("last_synced_id")
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"❌ 读取同步状态文件时出错：{e}")
        return None

def save_sync_state(state_file_path, last_synced_id):
    """保存最新的同步状态"""
    try:
        with open(state_file_path, "w", encoding="utf-8") as f:
            json.dump({"last_synced_id": last_synced_id}, f, indent=4)
        logging.info(f"✔ 同步状态已保存。最新帖子 ID: {last_synced_id}")
    except IOError as e:
        logging.error(f"❌ 无法写入同步状态文件：{e}")

def fetch_mastodon_posts(config, since_id=None, page_limit=None):
    """从 Mastodon API 获取帖子，page_limit 参数控制获取的页数"""
    mastodon_config = config["mastodon"]
    instance_url = mastodon_config["instance_url"]
    user_id = mastodon_config["user_id"]
    access_token = mastodon_config["access_token"]
    
    api_url = f"{instance_url}/api/v1/accounts/{user_id}/statuses"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "limit": 40,
        "exclude_replies": False,
        "exclude_reblogs": True,
    }
    if since_id:
        params["since_id"] = since_id

    all_posts = []
    page_count = 1
    
    while api_url:
        try:
            logging.info(f"📄 正在获取第 {page_count} 页...")
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            posts = response.json()
            if not posts:
                break
            all_posts.extend(posts)
            
            if page_limit and page_count >= page_limit:
                break

            if 'Link' in response.headers and 'next' in response.headers['Link']:
                links = requests.utils.parse_header_links(response.headers['Link'])
                api_url = next((link['url'] for link in links if link.get('rel') == 'next'), None)
                params.pop('since_id', None)
                page_count += 1
            else:
                api_url = None
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ API 请求失败：{e}")
            return []
            
    all_posts.reverse()
    return all_posts

def download_media(media_item, media_folder_path):
    """下载单个媒体文件，如果文件已存在则跳过"""
    try:
        parsed_url = urlparse(media_item['url'])
        original_filename = Path(parsed_url.path).name
        local_filename = f"{media_item['id']}-{original_filename}"
        local_file_path = media_folder_path / local_filename

        if not local_file_path.exists():
            logging.info(f"⬇️  正在下载媒体文件：{media_item['url']}")
            response = requests.get(media_item['url'], stream=True)
            response.raise_for_status()
            with open(local_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 下载媒体文件失败：{media_item['url']} - {e}")
        return None

def format_single_post_for_archive(post, media_folder_name, media_file_map):
    """将单个帖子格式化为归档文件中的一个条目"""
    utc_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    cst_tz = timezone(timedelta(hours=8))
    cst_dt = utc_dt.astimezone(cst_tz)
    time_str = cst_dt.strftime("%H:%M")

    is_reply = post.get("in_reply_to_id")
    if is_reply:
        icon = "💬"
        reply_to_user = ""
        if post.get("mentions"):
            reply_to_user = f"给 @{post['mentions'][0]['acct']}"
        heading = f"## {time_str} {icon} 回复{reply_to_user}"
        source_link_text = "**回复嘟文**"
    else:
        icon = "📝"
        heading = f"## {time_str} {icon} 嘟文"
        source_link_text = "**原始嘟文**"

    content_md = md(post["content"], heading_style="ATX").strip()
    source_link_part = f"{source_link_text}\uFF1A{post['url']}"
    content_part = f"**内容**\uFF1A{content_md}"
    
    attachments_md = ""
    if post["media_attachments"]:
        if content_md:
            attachments_md += "\n\n" # 与内容文本隔开
        
        media_parts = []
        for media in post["media_attachments"]:
            local_filename = media_file_map.get(media['id'])
            if local_filename:
                media_path = f"{media_folder_name}/{local_filename}"
                if media["type"] == "image":
                    media_parts.append(f"![{media.get('description') or 'Image'}]({media_path})")
                else:
                    media_parts.append(f"[{'观看视频' if media['type'] in ['video', 'gifv'] else '查看附件'}]({media_path})")
        attachments_md += "\n".join(media_parts)

    return f"{heading}\n\n{content_part}{attachments_md}\n\n{source_link_part}\n\n---\n\n"

def format_post_for_single_file(post, media_folder_name, media_file_map):
    """将单个帖子格式化为独立的 Markdown 文件内容"""
    utc_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    cst_tz = timezone(timedelta(hours=8))
    cst_dt = utc_dt.astimezone(cst_tz)
    created_at_str = cst_dt.strftime("%Y-%m-%d %H:%M:%S")

    tags = [f"#{tag['name']}" for tag in post["tags"]]
    
    frontmatter = {
        "id": post["id"],
        "createdAt": created_at_str,
        "source": post["url"],
        "type": "reply" if post["in_reply_to_id"] else "toot",
        "tags": tags,
    }
    if post["in_reply_to_id"]:
        frontmatter["inReplyToId"] = post["in_reply_to_id"]
        frontmatter["inReplyToAccountId"] = post["in_reply_to_account_id"]

    yaml_frontmatter = "---\n" + yaml.dump(frontmatter, allow_unicode=True) + "---\n\n"
    content_md = md(post["content"], heading_style="ATX")
    
    attachments_md = ""
    if post["media_attachments"]:
        attachments_md += "\n## 附件\n"
        for media in post["media_attachments"]:
            local_filename = media_file_map.get(media['id'])
            if local_filename:
                media_path = f"../{media_folder_name}/{local_filename}"
                if media["type"] == "image":
                    attachments_md += f"![{media.get('description') or 'Image'}]({media_path})\n"
                else:
                    attachments_md += f"[{'观看视频' if media['type'] in ['video', 'gifv'] else '查看附件'}]({media_path})\n"

    return yaml_frontmatter + content_md + attachments_md

def group_posts_by_day(posts):
    """将帖子按日期（CST）分组"""
    daily_posts = defaultdict(list)
    cst_tz = timezone(timedelta(hours=8))
    for post in posts:
        utc_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        cst_dt = utc_dt.astimezone(cst_tz)
        date_str = cst_dt.strftime("%Y-%m-%d")
        daily_posts[date_str].append(post)
    return daily_posts

def update_archive_file(posts_to_update, config, all_posts_from_server):
    """智能地更新或创建总的归档文件，避免重复和处理删除"""
    backup_config = config["backup"]
    backup_path = Path(backup_config["path"])
    media_folder_name = backup_config["media_folder"]
    archive_file_path = backup_path / backup_config["archive_filename"]
    
    # 1. 解析现有文件内容到按 post_id 组织的字典中
    existing_posts_by_id = {}
    if archive_file_path.exists():
        with open(archive_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 按分隔符分割成单个帖子的块
            post_blocks = content.split('---\n')
            for block in post_blocks:
                if not block.strip():
                    continue
                # 从链接中提取 post_id
                match = re.search(r'https://[^\/]+\/[^\/]+\/(\d+)', block)
                if match:
                    post_id = match.group(1)
                    existing_posts_by_id[post_id] = block

    # 2. 将新帖子和已编辑的帖子更新到字典中
    for post in posts_to_update:
        formatted_post = format_single_post_for_archive(post, media_folder_name, config["media_file_map"])
        # 保持完整的格式，包括分隔符
        existing_posts_by_id[post['id']] = formatted_post.strip()

    # 3. (仅增量同步) 检查并移除已删除的帖子
    if not config.get("is_full_sync", False):
        server_post_ids = {p['id'] for p in all_posts_from_server}
        local_post_ids = set(existing_posts_by_id.keys())
        
        deleted_ids = local_post_ids - server_post_ids
        if deleted_ids:
            logging.info(f"🗑️ 检测到 {len(deleted_ids)} 条已删除的帖子，将从归档中移除。")
            for post_id in deleted_ids:
                if post_id in existing_posts_by_id:
                    del existing_posts_by_id[post_id]

    # 4. 从字典重新生成帖子列表并按日期分组
    rebuilt_posts_by_day = defaultdict(list)
    
    all_posts_dict = {p['id']: p for p in all_posts_from_server}
    
    for post_id, content in existing_posts_by_id.items():
        if post_id in all_posts_dict:
            post_data = all_posts_dict[post_id]
            utc_dt = datetime.strptime(post_data["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            cst_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
            date_str = cst_dt.strftime("%Y-%m-%d")
            rebuilt_posts_by_day[date_str].append({'content': content, 'created_at': post_data['created_at']})

    # 5. 从分组后的帖子重新构建整个文件内容
    final_content = ""
    for date_str in sorted(rebuilt_posts_by_day.keys(), reverse=True):
        final_content += f"# {date_str}\n\n"
        day_posts = sorted(rebuilt_posts_by_day[date_str], key=lambda p: p['created_at'], reverse=True)
        # 使用 --- 分隔符重新连接帖子
        final_content += '\n'.join([p['content'] for p in day_posts])
        final_content += '\n\n'
            
    # 6. 将完全更新后的内容写回文件
    with open(archive_file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    logging.info(f"✍️  已更新归档文件：{archive_file_path}")

def save_posts(posts, config, all_posts_from_server):
    """同时更新归档文件和独立的帖子文件"""
    backup_config = config["backup"]
    backup_path = Path(backup_config["path"])
    
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]
    
    media_file_map = {}
    media_folder_created = False
    for post in posts:
        if post.get("media_attachments"):
            if not media_folder_created:
                media_folder_path.mkdir(parents=True, exist_ok=True)
                media_folder_created = True
            
            for media in post["media_attachments"]:
                local_filename = download_media(media, media_folder_path)
                if local_filename:
                    media_file_map[media['id']] = local_filename
    
    config["media_file_map"] = media_file_map

    update_archive_file(posts, config, all_posts_from_server)

    posts_folder_path.mkdir(parents=True, exist_ok=True)
    for post in posts:
        utc_dt = datetime.strptime(post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        cst_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        filename_date = cst_dt.strftime("%Y-%m-%d_%H%M%S")
        filename = f"{filename_date}_{post['id']}.md"
        file_path = posts_folder_path / filename
        
        new_content = format_post_for_single_file(post, backup_config["media_folder"], media_file_map)
        
        should_write = True
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
            if old_content == new_content:
                should_write = False

        if should_write:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logging.info(f"📄 已备份/更新单条嘟文：{file_path}")
            except IOError as e:
                logging.error(f"❌ 无法写入文件 {file_path}: {e}")

def cleanup_deleted_posts(config):
    """清理在服务器上已被删除的帖子"""
    logging.info("🧹 开始执行清理模式...")
    backup_config = config["backup"]
    backup_path = Path(backup_config["path"])
    posts_folder_path = backup_path / backup_config["posts_folder"]
    
    if not posts_folder_path.exists():
        logging.info("✅ 未发现本地帖子文件夹，无需清理。")
        return

    logging.info("🚀 正在获取服务器上的所有帖子 ID...")
    all_server_posts = fetch_mastodon_posts(config, page_limit=None)
    server_post_ids = {p['id'] for p in all_server_posts}
    logging.info(f"服务器上共有 {len(server_post_ids)} 条帖子。")

    local_post_files = list(posts_folder_path.glob("*.md"))
    deleted_count = 0
    for file_path in local_post_files:
        match = re.search(r'_(\d+)\.md$', file_path.name)
        if match:
            post_id = match.group(1)
            if post_id not in server_post_ids:
                logging.info(f"🗑️  正在删除本地文件：{file_path.name}")
                file_path.unlink()
                deleted_count += 1
    
    logging.info(f"✅ 清理完成，共删除了 {deleted_count} 个已不存在的帖子备份。")
    logging.warning("⚠️  请注意：清理模式只删除了单条备份文件。要更新汇总文件，请运行一次强制全量同步。")


def main():
    """主执行函数"""
    logging.info("========================================")
    logging.info(" Mastodon Sync 开始运行")
    logging.info("========================================")
    
    config = get_config()
    
    if "--cleanup" in sys.argv:
        cleanup_deleted_posts(config)
        logging.info("========================================")
        logging.info(" ✅ 清理完成！")
        logging.info("========================================")
        return

    state_file_path = Path(config["sync"]["state_file"])
    
    backup_config = config["backup"]
    backup_path = Path(backup_config["path"])
    archive_filename = backup_config["archive_filename"]
    archive_file_path = backup_path / archive_filename
    posts_folder_path = backup_path / backup_config["posts_folder"]
    media_folder_path = backup_path / backup_config["media_folder"]

    is_action_full_sync = os.environ.get("FORCE_FULL_SYNC") == "true"
    is_cli_full_sync = "--full-sync" in sys.argv
    is_automatic_full_sync = not archive_file_path.exists()
    
    is_full_sync = is_action_full_sync or is_cli_full_sync or is_automatic_full_sync
    config["is_full_sync"] = is_full_sync
    last_synced_id = None
    
    if is_full_sync:
        if is_action_full_sync:
             logging.warning("⚠️  检测到手动触发全量同步，将执行全量同步。")
        elif is_cli_full_sync:
            logging.warning("⚠️  检测到 --full-sync 参数，将强制执行全量同步。")
        else:
            logging.warning(f"⚠️  检测到 '{archive_filename}' 文件不存在，将自动执行全量同步。")
        
        if state_file_path.exists():
            state_file_path.unlink()
            logging.info("ℹ️  已删除旧的同步状态文件。")
        if archive_file_path.exists():
            archive_file_path.unlink()
            logging.info(f"ℹ️  已删除旧的归档文件 '{archive_filename}'。")
        if posts_folder_path.exists():
            shutil.rmtree(posts_folder_path)
            logging.info(f"ℹ️  已删除旧的单条嘟文文件夹 '{posts_folder_path.name}'。")
        if media_folder_path.exists():
            shutil.rmtree(media_folder_path)
            logging.info(f"ℹ️  已删除旧的媒体文件夹 '{media_folder_path.name}'。")
    else:
        last_synced_id = load_sync_state(state_file_path)
        if last_synced_id:
            logging.info(f"ℹ️  当前为增量同步模式，将获取 ID 在 {last_synced_id} 之后的新帖子。")
    
    posts_to_process = []
    all_posts_from_server_for_sync = []
    if is_full_sync:
        logging.info("🚀 开始全量获取帖子...")
        posts_to_process = fetch_mastodon_posts(config, page_limit=None)
        all_posts_from_server_for_sync = posts_to_process
    else:
        logging.info("🚀 开始增量获取新帖子...")
        new_posts = fetch_mastodon_posts(config, since_id=last_synced_id, page_limit=None)
        
        logging.info("🔄 正在检查最近的帖子是否有编辑...")
        check_limit = backup_config["check_edit_limit"]
        num_pages_to_check = (check_limit + 39) // 40
        recent_posts = fetch_mastodon_posts(config, page_limit=num_pages_to_check)
        all_posts_from_server_for_sync = recent_posts
        
        posts_dict = {p['id']: p for p in new_posts}
        for p in recent_posts:
            posts_dict[p['id']] = p
            
        posts_to_process = sorted(list(posts_dict.values()), key=lambda p: p['created_at'])

    if not posts_to_process:
        logging.info("✨ 没有新内容需要同步。")
    else:
        save_posts(posts_to_process, config, all_posts_from_server_for_sync)
        
        all_ids = [p['id'] for p in posts_to_process]
        if last_synced_id and not is_full_sync:
            all_ids.append(last_synced_id)
        
        if all_ids:
            new_last_synced_id = max(all_ids, key=int)
            save_sync_state(state_file_path, new_last_synced_id)

    logging.info("========================================")
    logging.info(" ✅ 同步完成！")
    logging.info("========================================")

if __name__ == "__main__":
    main()