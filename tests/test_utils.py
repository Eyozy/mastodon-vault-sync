# -*- coding: utf-8 -*-
"""工具函数测试"""
from datetime import datetime

from src.utils import get_timezone_aware_datetime, parse_rate_limit_reset


def test_get_timezone_aware_datetime_utc():
    """测试 UTC 时区转换"""
    result = get_timezone_aware_datetime(
        "2024-01-01T12:00:00.000Z", china_timezone=False
    )
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1


def test_get_timezone_aware_datetime_china():
    """测试中国时区转换"""
    result = get_timezone_aware_datetime(
        "2024-01-01T12:00:00.000Z", china_timezone=True
    )
    assert isinstance(result, datetime)
    assert result.year == 2024


def test_parse_rate_limit_reset_unix():
    """测试解析 Unix 时间戳"""
    result = parse_rate_limit_reset("1704110400")
    assert result == 1704110400


def test_parse_rate_limit_reset_invalid():
    """测试解析无效时间戳"""
    result = parse_rate_limit_reset("invalid")
    assert result is None


def test_parse_rate_limit_reset_none():
    """测试解析 None"""
    result = parse_rate_limit_reset(None)
    assert result is None
