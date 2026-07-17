# -*- coding: utf-8 -*-
import re
from typing import Any, Dict

import yaml
from markdownify import markdownify as md

from ..utils import get_timezone_aware_datetime


def strip_autolinks(text: str) -> str:
    return re.sub(r"<(https?://[^>]+)>", r"\1", text)


def format_single_post_for_archive(
    post: Dict[str, Any],
    media_folder_name: str,
    media_file_map: Dict[str, str],
    china_timezone: bool = False,
) -> str:
    local_dt = get_timezone_aware_datetime(post["created_at"], china_timezone)
    time_str = local_dt.strftime("%H:%M")
    is_reply = post.get("in_reply_to_id")
    icon = "💬" if is_reply else "📝"
    heading = f"## {time_str} {icon} {'回复' if is_reply else '嘟文'}"
    source_link_text = "**回复嘟文**" if is_reply else "**原始嘟文**"
    content_md = strip_autolinks(md(post["content"], heading_style="ATX")).strip()
    attachments_md = ""
    if post["media_attachments"]:
        media_parts = []
        for media in post["media_attachments"]:
            if local_filename := media_file_map.get(media["id"]):
                media_path = f"{media_folder_name}/{local_filename}"
                media_parts.append(
                    f"![{media.get('description') or 'Image'}]({media_path})"
                )
        if media_parts:
            attachments_md = ("\n\n" if content_md else "") + "\n".join(media_parts)
    return f"{heading}\n\n**内容**：{content_md}{attachments_md}\n\n{source_link_text}：{post['url']}\n\n---\n\n"


def format_post_for_single_file(
    post: Dict[str, Any],
    media_folder_name: str,
    media_file_map: Dict[str, str],
    china_timezone: bool = False,
) -> str:
    local_dt = get_timezone_aware_datetime(post["created_at"], china_timezone)
    in_reply_to_id = post.get("in_reply_to_id")
    frontmatter = {
        "id": post["id"],
        "date": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "source": post["url"],
        "type": "reply" if in_reply_to_id else "toot",
        "visibility": post.get("visibility", "public"),
        "hasMedia": bool(post.get("media_attachments", [])),
        "tags": [tag["name"] for tag in post.get("tags", [])],
    }
    if in_reply_to_id:
        frontmatter.update(
            {
                "inReplyToId": in_reply_to_id,
                "inReplyToAccountId": post.get("in_reply_to_account_id"),
            }
        )
    yaml_frontmatter = "---\n" + yaml.dump(frontmatter, allow_unicode=True) + "---\n\n"
    content_md = strip_autolinks(md(post["content"], heading_style="ATX"))
    attachments_md = ""
    if post["media_attachments"]:
        media_parts = []
        for media in post["media_attachments"]:
            if local_filename := media_file_map.get(media["id"]):
                media_path = f"../{media_folder_name}/{local_filename}"
                media_parts.append(
                    f"![{media.get('description') or 'Image'}]({media_path})\n"
                )
        if media_parts:
            attachments_md = "\n## 附件\n" + "".join(media_parts)
    return yaml_frontmatter + content_md + attachments_md
