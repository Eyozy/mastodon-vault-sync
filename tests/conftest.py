# -*- coding: utf-8 -*-
"""pytest 配置和 fixtures"""
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_config(temp_dir):
    """示例配置 fixture"""
    return {
        "mastodon": {
            "instance_url": "https://mastodon.example",
            "user_id": "123456",
            "access_token": "test_token",
        },
        "backup": {
            "path": str(temp_dir),
            "posts_folder": "mastodon",
            "filename": "archive.md",
            "media_folder": "media",
            "summary_filename": "activity_summary.md",
            "html_filename": "index.html",
        },
        "sync": {"state_file": "sync_state.json", "china_timezone": False},
    }


@pytest.fixture
def make_post():
    """构造满足同步流程的 Mastodon 帖子数据"""

    def _make_post(post_id: str, created_at: str, content: str) -> dict:
        return {
            "id": post_id,
            "created_at": created_at,
            "content": f"<p>{content}</p>",
            "url": f"https://example.com/@test/{post_id}",
            "media_attachments": [],
            "tags": [],
            "sensitive": False,
            "spoiler_text": "",
            "visibility": "public",
            "reblogs_count": 0,
            "favourites_count": 0,
            "replies_count": 0,
            "emojis": [],
            "in_reply_to_id": None,
            "in_reply_to_account_id": None,
            "account": {
                "id": "1",
                "username": "test",
                "display_name": "Test User",
                "avatar": "https://example.com/avatar.png",
                "url": "https://example.com/@test",
                "note": "Test bio",
                "header": "",
                "followers_count": 5,
                "following_count": 3,
            },
        }

    return _make_post
