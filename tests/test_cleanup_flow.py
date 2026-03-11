# -*- coding: utf-8 -*-
"""cleanup 主流程测试"""
import json

import pytest

import main
from src.backup import save_posts


@pytest.mark.asyncio
async def test_cleanup_removes_deleted_posts_and_stale_media(
    temp_dir, make_post, monkeypatch
):
    backup_path = temp_dir / "backup"
    state_file = temp_dir / "sync_state.json"
    config = {
        "mastodon": {
            "instance_url": "https://example.com",
            "user_id": "1",
            "access_token": "test_token_12345",
        },
        "backup": {
            "path": str(backup_path),
            "posts_folder": "mastodon",
            "filename": "archive.md",
            "media_folder": "media",
            "summary_filename": "activity_summary.md",
            "html_filename": "index.html",
        },
        "sync": {"state_file": str(state_file), "china_timezone": False},
    }

    post_a = make_post("100", "2024-01-01T10:00:00.000Z", "第一条")
    post_b = make_post("101", "2024-01-02T10:00:00.000Z", "第二条")
    post_c = make_post("102", "2024-01-03T10:00:00.000Z", "第三条")

    await save_posts(
        [post_a, post_b, post_c], config, [post_a, post_b, post_c], backup_path
    )
    state_file.write_text(json.dumps({"last_synced_id": "102"}), encoding="utf-8")

    stale_media = backup_path / "media" / "stale.bin"
    stale_media.parent.mkdir(parents=True, exist_ok=True)
    stale_media.write_bytes(b"stale")

    async def fake_fetch(config, since_id=None, page_limit=None, max_posts=None):
        _ = config, since_id, page_limit, max_posts
        return [post_a, post_c]

    monkeypatch.setattr(main, "get_config", lambda: config)
    monkeypatch.setattr(main, "fetch_mastodon_posts", fake_fetch)
    monkeypatch.setattr(main.sys, "argv", ["main.py", "--cleanup"])

    await main.main_async()

    posts_folder = backup_path / "mastodon"
    remaining_files = sorted(path.name for path in posts_folder.glob("*.md"))
    archive_content = (backup_path / "archive.md").read_text(encoding="utf-8")

    assert len(remaining_files) == 2
    assert all("101" not in file_name for file_name in remaining_files)
    assert "第一条" in archive_content
    assert "第三条" in archive_content
    assert "第二条" not in archive_content
    assert not stale_media.exists()
    assert json.loads(state_file.read_text(encoding="utf-8"))["last_synced_id"] == "102"
