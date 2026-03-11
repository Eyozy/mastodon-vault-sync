# -*- coding: utf-8 -*-
"""同步主流程端到端测试"""
import json

import pytest

import main


@pytest.mark.asyncio
async def test_main_async_preserves_history_across_full_and_incremental_sync(
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

    async def fake_fetch(config, since_id=None, page_limit=None, max_posts=None):
        _ = config, max_posts
        if since_id == "101":
            return [post_c]
        if page_limit == 5:
            return [post_b, post_c]
        if state_file.exists():
            return [post_a, post_b, post_c]
        return [post_a, post_b]

    monkeypatch.setattr(main, "get_config", lambda: config)
    monkeypatch.setattr(main, "fetch_mastodon_posts", fake_fetch)
    monkeypatch.setattr(main.sys, "argv", ["main.py", "sync"])

    await main.main_async()

    posts_folder = backup_path / "mastodon"
    archive_file = backup_path / "archive.md"
    html_file = backup_path / "index.html"
    summary_file = backup_path / "activity_summary.md"

    assert posts_folder.exists()
    assert len(list(posts_folder.glob("*.md"))) == 2
    assert archive_file.exists()
    assert html_file.exists()
    assert summary_file.exists()
    assert json.loads(state_file.read_text(encoding="utf-8"))["last_synced_id"] == "101"

    await main.main_async()

    archive_content = archive_file.read_text(encoding="utf-8")
    assert len(list(posts_folder.glob("*.md"))) == 3
    assert "第一条" in archive_content
    assert "第二条" in archive_content
    assert "第三条" in archive_content
    assert json.loads(state_file.read_text(encoding="utf-8"))["last_synced_id"] == "102"
