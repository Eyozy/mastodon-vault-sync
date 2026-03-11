# -*- coding: utf-8 -*-
"""备份逻辑测试"""
from src.backup import update_archive_file


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
