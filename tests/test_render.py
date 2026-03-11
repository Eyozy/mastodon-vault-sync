# -*- coding: utf-8 -*-
"""渲染功能测试"""
from pathlib import Path

import pytest

from src.render import (
    format_single_post_for_archive,
    generate_html_template,
    generate_mastodon_html,
    get_default_css,
    strip_autolinks,
    validate_post_data,
)


@pytest.fixture
def sample_post():
    """示例帖子数据"""
    return {
        "id": "123",
        "created_at": "2024-01-01T12:00:00.000Z",
        "content": "<p>测试帖子</p>",
        "account": {
            "username": "testuser",
            "display_name": "Test User",
            "avatar": "https://example.com/avatar.jpg",
        },
        "media_attachments": [],
        "tags": [{"name": "test"}],
        "favourites_count": 5,
        "reblogs_count": 2,
        "replies_count": 1,
        "url": "https://example.com/@testuser/123",
    }


def test_strip_autolinks():
    """测试移除自动链接"""
    text = "Check <https://example.com> out"
    result = strip_autolinks(text)
    assert result == "Check https://example.com out"


def test_validate_post_data_valid(sample_post):
    """测试验证有效的帖子数据"""
    assert validate_post_data(sample_post) is True


def test_validate_post_data_invalid():
    """测试验证无效的帖子数据"""
    invalid_post = {"id": "123"}
    assert validate_post_data(invalid_post) is False


def test_format_single_post_for_archive(sample_post):
    """测试格式化单个帖子为归档格式"""
    result = format_single_post_for_archive(
        sample_post, media_folder_name="media", media_file_map={}, china_timezone=False
    )
    assert "测试帖子" in result
    assert "原始嘟文" in result
    assert "---" in result


def test_get_default_css():
    """测试获取默认 CSS"""
    css = get_default_css()
    assert len(css) > 0
    assert "body" in css or "html" in css


def test_generate_html_template_escapes_profile_fields_and_serializes_posts_safely():
    """HTML 模板应转义资料字段，并安全嵌入帖子 JSON"""
    html = generate_html_template(
        username='alice"><script>alert(1)</script>',
        display_name="<b>Alice</b>",
        avatar='https://example.com/avatar.png" onerror="alert(1)',
        instance_name="example.social",
        background_image='https://example.com/bg.jpg");alert(1);/*',
        total_posts=1,
        followers_count=2,
        following_count=3,
        posts_data=[
            {
                "id": "1",
                "content": "</script><script>alert(1)</script>",
                "created_at": "2024-01-01 12:00:00",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "url": "https://example.com/@alice/1",
                "sensitive": False,
                "spoiler_text": "",
                "visibility": "public",
                "media_attachments": [],
                "reblogs_count": 0,
                "favourites_count": 0,
                "replies_count": 0,
                "in_reply_to_id": None,
                "in_reply_to_account_id": None,
                "account": {
                    "id": "1",
                    "username": "alice",
                    "display_name": "Alice",
                    "url": "https://example.com/@alice",
                    "avatar": "https://example.com/avatar.png",
                },
                "tags": [],
            }
        ],
        user_bio="<img src=x onerror=alert(1)>",
    )

    assert "&lt;b&gt;Alice&lt;/b&gt;" in html
    assert "<b>Alice</b>" not in html
    assert 'id="posts-data"' in html
    assert 'JSON.parse(document.getElementById("posts-data").textContent)' in html
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script><script>alert(1)<\\/script>" in html


def test_generate_mastodon_html_uses_timeouts_for_remote_assets(tmp_path, monkeypatch):
    """远程背景图和 emoji 请求应显式设置超时"""
    timeouts = []

    class DummyResponse:
        status_code = 404
        headers = {"Content-Type": "image/png"}
        content = b""

        def iter_content(self, chunk_size):
            return iter(())

    def fake_get(url, **kwargs):
        timeouts.append(kwargs.get("timeout"))
        return DummyResponse()

    monkeypatch.setattr("src.render.requests.get", fake_get)

    post = {
        "id": "123",
        "created_at": "2024-01-01T12:00:00.000Z",
        "content": "<p>测试帖子</p>",
        "url": "https://example.com/@test/123",
        "sensitive": False,
        "spoiler_text": "",
        "visibility": "public",
        "media_attachments": [],
        "reblogs_count": 0,
        "favourites_count": 0,
        "replies_count": 0,
        "in_reply_to_id": None,
        "in_reply_to_account_id": None,
        "tags": [],
        "emojis": [{"shortcode": "wave", "url": "https://example.com/wave.png"}],
        "account": {
            "id": "1",
            "username": "test",
            "display_name": "Test",
            "avatar": "https://example.com/avatar.png",
            "url": "https://example.com/@test",
            "note": "hello",
            "header": "https://example.com/header.jpg",
            "followers_count": 1,
            "following_count": 2,
        },
    }
    config = {
        "backup": {"html_filename": "index.html", "media_folder": "media"},
        "sync": {"china_timezone": False},
    }

    generate_mastodon_html([post], config, Path(tmp_path))

    assert timeouts
    assert all(timeout is not None for timeout in timeouts)
