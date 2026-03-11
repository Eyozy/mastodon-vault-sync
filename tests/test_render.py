# -*- coding: utf-8 -*-
"""渲染功能测试"""
import pytest

from src.render import (
    format_single_post_for_archive,
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
