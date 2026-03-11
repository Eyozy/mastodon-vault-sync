# -*- coding: utf-8 -*-
"""pytest 配置和 fixtures"""
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_config(temp_dir):
    """示例配置 fixture"""
    return {
        "mastodon": {
            "instance_url": "https://mastodon.example",
            "user_id": "123456",
            "access_token": "test_token",
        },
        "backup": {
            "path": str(temp_dir),
            "posts_folder": "mastodon",
            "filename": "archive.md",
            "media_folder": "media",
            "summary_filename": "activity_summary.md",
            "html_filename": "index.html",
        },
        "sync": {"state_file": "sync_state.json", "china_timezone": False},
    }
