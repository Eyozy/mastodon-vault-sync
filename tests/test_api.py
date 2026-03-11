# -*- coding: utf-8 -*-
"""API 调用测试"""
import aiohttp
import pytest

from src.api import (
    DEFAULT_WAIT_TIME,
    POSTS_PER_REQUEST,
    RATE_LIMIT_THRESHOLD,
    fetch_mastodon_posts,
)


def test_posts_per_request_constant():
    """测试 API 常量配置"""
    assert POSTS_PER_REQUEST == 40


def test_rate_limit_threshold():
    """测试速率限制阈值"""
    assert RATE_LIMIT_THRESHOLD == 10


def test_default_wait_time():
    """测试默认等待时间"""
    assert DEFAULT_WAIT_TIME == 300


@pytest.mark.asyncio
async def test_fetch_mastodon_posts_retries_transient_client_errors(monkeypatch):
    """API 临时失败时应重试，而不是直接返回空列表"""
    attempts = 0
    sample_post = {
        "id": "123",
        "created_at": "2024-01-01T12:00:00.000Z",
        "content": "<p>测试</p>",
        "account": {"id": "1", "username": "test"},
        "media_attachments": [],
        "tags": [],
        "url": "https://example.com/@test/123",
    }

    class FakeResponse:
        headers = {
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Reset": "0",
            "Link": "",
        }

        def raise_for_status(self):
            return None

        async def json(self):
            return [sample_post]

    class FakeRequest:
        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise aiohttp.ClientError("temporary failure")
            return FakeResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, api_url, headers=None, params=None):
            _ = api_url, headers, params
            return FakeRequest()

    monkeypatch.setattr(
        "src.api.aiohttp.ClientSession", lambda connector=None: FakeSession()
    )
    monkeypatch.setattr("src.api.aiohttp.TCPConnector", lambda ssl=True: object())
    monkeypatch.setattr("src.api.RETRY_BASE_DELAY_SECONDS", 0)

    config = {
        "mastodon": {
            "instance_url": "https://example.com",
            "user_id": "1",
            "access_token": "token_1234567890",
        }
    }

    posts = await fetch_mastodon_posts(config)

    assert [post["id"] for post in posts] == ["123"]
    assert attempts == 3
