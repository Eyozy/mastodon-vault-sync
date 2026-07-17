# -*- coding: utf-8 -*-
import logging
import os
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class MastodonConfig(BaseModel):
    instance_url: str = Field(..., description="Mastodon instance URL")
    user_id: int = Field(..., description="User ID (numeric)")
    access_token: str = Field(..., min_length=10, description="Access token")

    @field_validator("instance_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return v.rstrip("/")


class BackupConfig(BaseModel):
    path: str = Field(default=".", description="Backup root path")
    filename: str = "archive.md"
    posts_folder: str = "mastodon"
    media_folder: str = "media"
    summary_filename: str = "README.md"
    html_filename: str = "index.html"


class SyncConfig(BaseModel):
    state_file: str = "sync_state.json"
    china_timezone: bool = False


class AppConfig(BaseModel):
    mastodon: MastodonConfig
    backup: BackupConfig = Field(default_factory=BackupConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)
    # 运行时字段（如 is_full_sync、media_file_map）允许透传
    model_config = {"extra": "allow"}


def validate_config(config: Dict[str, Any]) -> AppConfig:
    """入口校验：只在加载配置时用 pydantic，业务层继续使用 dict。"""
    try:
        app_config = AppConfig(**config)
        logging.info("✔ 配置验证通过")
        return app_config
    except ValidationError as e:
        logging.error(f"❌ 配置验证失败：{e}")
        raise ValueError(f"Configuration validation failed: {e}")


def get_config() -> Dict[str, Any]:
    """加载配置，校验后返回 dict，兼容现有可变运行时字段。"""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        logging.info("✔ 检测到 GitHub Actions 环境，使用环境变量配置。")
        config_data = {
            "mastodon": {
                "instance_url": os.environ.get("MASTODON_INSTANCE_URL"),
                "user_id": os.environ.get("MASTODON_USER_ID"),
                "access_token": os.environ.get("MASTODON_ACCESS_TOKEN"),
            },
            "backup": {
                "path": ".",
                "filename": os.environ.get("ARCHIVE_FILENAME") or "archive.md",
                "posts_folder": os.environ.get("POSTS_FOLDER") or "mastodon",
                "media_folder": os.environ.get("MEDIA_FOLDER") or "media",
                "summary_filename": os.environ.get("SUMMARY_FILENAME") or "README.md",
                "html_filename": os.environ.get("HTML_FILENAME") or "index.html",
            },
            "sync": {
                "state_file": "sync_state.json",
                "china_timezone": os.environ.get("CHINA_TIMEZONE", "false").lower()
                == "true",
            },
        }
    else:
        logging.info("✔ 本地运行模式，尝试从 config.yaml 文件加载。")
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
            logging.info("✔ 配置文件加载成功。")
        except FileNotFoundError:
            logging.error("❌ 错误：找不到 config.yaml 文件。")
            raise
        except yaml.YAMLError as e:
            logging.error(f"❌ 错误：配置文件格式错误：{e}")
            raise

    return validate_config(config_data).model_dump()
