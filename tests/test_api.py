# -*- coding: utf-8 -*-
"""API 调用测试"""
from src.api import DEFAULT_WAIT_TIME, POSTS_PER_REQUEST, RATE_LIMIT_THRESHOLD


def test_posts_per_request_constant():
    """测试 API 常量配置"""
    assert POSTS_PER_REQUEST == 40


def test_rate_limit_threshold():
    """测试速率限制阈值"""
    assert RATE_LIMIT_THRESHOLD == 10


def test_default_wait_time():
    """测试默认等待时间"""
    assert DEFAULT_WAIT_TIME == 300
