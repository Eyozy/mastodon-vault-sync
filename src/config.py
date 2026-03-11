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

    # Allow extra fields for runtime state (e.g. media_file_map, is_full_sync)
    model_config = {"extra": "allow"}


def validate_config(config: Dict[str, Any]) -> AppConfig:
    """
    Validates config dictionary using Pydantic model.
    Returns the validated AppConfig model.
    """
    try:
        app_config = AppConfig(**config)
        logging.info("✔ 配置验证通过")
        return app_config
    except ValidationError as e:
        logging.error(f"❌ 配置验证失败：{e}")
        raise ValueError(f"Configuration validation failed: {e}")


def get_config() -> Dict[str, Any]:
    """
    Loads configuration from environment or yaml file.
    Returns a dictionary for compatibility, but validated.
    """
    config_data = {}

    # GitHub Actions environment
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
        # Local environment
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

    # Validate and return as dict (for compatibility with existing mutable usage)
    # Ideally we should use the model object, but that requires more refactoring.
    # We dump it back to dict to ensure defaults are applied and types are coerced where possible,
    # but we need to match the structure expected by the rest of the app.
    validated_config = validate_config(config_data)
    return validated_config.model_dump()
