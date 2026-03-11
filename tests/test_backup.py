# -*- coding: utf-8 -*-
"""备份逻辑测试"""
import asyncio

import pytest

from src.backup import (
    MEDIA_DOWNLOAD_CONCURRENCY,
    download_all_media,
    update_archive_file,
)
from src.render import format_post_for_single_file


def test_update_archive_file(tmp_path):
    """测试更新归档文件"""
    backup_path = tmp_path / "vault"
    backup_path.mkdir()

    posts = [
        {
            "id": "123",
            "created_at": "2024-01-01T12:00:00.000Z",
            "content": "<p>测试</p>",
            "account": {"username": "test"},
            "media_attachments": [],
            "tags": [],
            "url": "https://example.com/@test/123",
        }
    ]

    config = {
        "backup": {"media_folder": "media", "filename": "archive.md"},
        "sync": {"china_timezone": False},
        "media_file_map": {},
    }

    update_archive_file(posts, config, posts, backup_path)
    archive_file = backup_path / "archive.md"
    assert archive_file.exists()
    content = archive_file.read_text(encoding="utf-8")
    assert "测试" in content


def test_update_archive_file_with_existing(tmp_path):
    """测试更新已存在的归档文件"""
    backup_path = tmp_path / "vault"
    backup_path.mkdir()

    # 创建已存在的归档文件
    archive_file = backup_path / "archive.md"
    archive_file.write_text(
        "## 12:00 📝 嘟文\n\n**内容**：旧帖子\n\n**原始嘟文**：https://example.com/@test/999\n\n---\n\n",
        encoding="utf-8",
    )

    posts = [
        {
            "id": "123",
            "created_at": "2024-01-01T12:00:00.000Z",
            "content": "<p>新帖子</p>",
            "account": {"username": "test"},
            "media_attachments": [],
            "tags": [],
            "url": "https://example.com/@test/123",
        }
    ]

    config = {
        "backup": {"media_folder": "media", "filename": "archive.md"},
        "sync": {"china_timezone": False},
        "media_file_map": {},
    }

    update_archive_file(posts, config, posts, backup_path)
    content = archive_file.read_text(encoding="utf-8")
    assert "新帖子" in content


def test_update_archive_file_preserves_history_outside_recent_window(tmp_path):
    """增量更新归档时，历史帖子不应因 recent window 缩小而丢失"""
    backup_path = tmp_path / "vault"
    posts_folder = backup_path / "mastodon"
    posts_folder.mkdir(parents=True)

    old_post = {
        "id": "999",
        "created_at": "2023-12-31T23:59:00.000Z",
        "content": "<p>旧帖子</p>",
        "account": {"username": "test"},
        "media_attachments": [],
        "tags": [],
        "url": "https://example.com/@test/999",
        "in_reply_to_id": None,
        "in_reply_to_account_id": None,
    }
    new_post = {
        "id": "123",
        "created_at": "2024-01-01T12:00:00.000Z",
        "content": "<p>新帖子</p>",
        "account": {"username": "test"},
        "media_attachments": [],
        "tags": [],
        "url": "https://example.com/@test/123",
        "in_reply_to_id": None,
        "in_reply_to_account_id": None,
    }

    old_post_path = posts_folder / "2023-12-31_235900_999.md"
    old_post_path.write_text(
        format_post_for_single_file(old_post, "media", {}, china_timezone=False),
        encoding="utf-8",
    )

    config = {
        "backup": {
            "media_folder": "media",
            "filename": "archive.md",
            "posts_folder": "mastodon",
        },
        "sync": {"china_timezone": False},
        "media_file_map": {},
    }

    update_archive_file([new_post], config, [new_post], backup_path)
    content = (backup_path / "archive.md").read_text(encoding="utf-8")

    assert "旧帖子" in content
    assert "新帖子" in content


@pytest.mark.asyncio
async def test_download_all_media_limits_concurrency(tmp_path, monkeypatch):
    """媒体下载应受并发限制，避免一次性打满连接数"""
    active = 0
    max_active = 0

    class DummySession:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def fake_download_media(session, media_item, media_folder_path):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return f"{media_item['id']}.png"

    monkeypatch.setattr(
        "src.backup.aiohttp.ClientSession", lambda connector=None: DummySession()
    )
    monkeypatch.setattr("src.backup.download_media", fake_download_media)

    media_items = [
        {"id": str(index), "url": f"https://example.com/{index}.png"}
        for index in range(MEDIA_DOWNLOAD_CONCURRENCY * 2 + 1)
    ]

    media_file_map = await download_all_media(media_items, tmp_path)

    assert len(media_file_map) == len(media_items)
    assert max_active <= MEDIA_DOWNLOAD_CONCURRENCY


@pytest.mark.asyncio
async def test_download_media_retries_transient_errors(tmp_path):
    """媒体下载遇到临时错误时应重试"""
    from src.backup import download_media

    attempts = 0
    media_item = {"id": "1", "url": "https://example.com/image.png"}

    class FakeContent:
        def __init__(self):
            self._sent = False

        async def read(self, chunk_size):
            _ = chunk_size
            if self._sent:
                return b""
            self._sent = True
            return b"data"

    class FakeResponse:
        def __init__(self):
            self.content = FakeContent()

        def raise_for_status(self):
            return None

    class FakeRequest:
        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError("temporary download error")
            return FakeResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def get(self, url):
            _ = url
            return FakeRequest()

    filename = await download_media(FakeSession(), media_item, tmp_path)

    assert filename == "1-image.png"
    assert attempts == 3
    assert (tmp_path / "1-image.png").read_bytes() == b"data"
