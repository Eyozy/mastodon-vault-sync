# -*- coding: utf-8 -*-
"""基础测试 - 确保核心功能不被破坏"""
import pytest

from src.config import validate_config


def test_validate_config_success(sample_config):
    """测试有效配置通过验证"""
    result = validate_config(sample_config)
    assert result is not None


def test_validate_config_missing_token(sample_config):
    """测试缺少令牌时验证失败"""
    del sample_config["mastodon"]["access_token"]
    with pytest.raises(ValueError):
        validate_config(sample_config)


def test_validate_config_missing_user_id(sample_config):
    """测试缺少用户 ID 时验证失败"""
    del sample_config["mastodon"]["user_id"]
    with pytest.raises(ValueError):
        validate_config(sample_config)


def test_validate_config_invalid_url(sample_config):
    """测试无效 URL 时验证失败"""
    sample_config["mastodon"]["instance_url"] = "not-a-url"
    with pytest.raises(ValueError):
        validate_config(sample_config)


def test_config_has_required_fields(sample_config):
    """测试配置包含所有必需字段"""
    assert "mastodon" in sample_config
    assert "backup" in sample_config
    assert "sync" in sample_config

    assert "instance_url" in sample_config["mastodon"]
    assert "user_id" in sample_config["mastodon"]
    assert "access_token" in sample_config["mastodon"]

    assert "path" in sample_config["backup"]
    assert "posts_folder" in sample_config["backup"]
    assert "filename" in sample_config["backup"]
    assert "media_folder" in sample_config["backup"]
