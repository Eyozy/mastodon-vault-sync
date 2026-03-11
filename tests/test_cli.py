# -*- coding: utf-8 -*-
"""CLI 集成测试"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_sync_command_dispatches_to_main():
    """sync 子命令应进入同步主流程"""
    result = run_cli("sync")
    combined_output = result.stdout + result.stderr
    assert "Mastodon Sync 开始运行" in combined_output
    assert "未知命令" not in combined_output


def test_sync_full_command_dispatches_to_main():
    """sync --full 应进入同步主流程"""
    result = run_cli("sync", "--full")
    combined_output = result.stdout + result.stderr
    assert "Mastodon Sync 开始运行" in combined_output
    assert "未知命令" not in combined_output


def test_cleanup_command_dispatches_to_main():
    """cleanup 子命令应进入同步主流程"""
    result = run_cli("cleanup")
    combined_output = result.stdout + result.stderr
    assert "Mastodon Sync 开始运行" in combined_output
    assert "未知命令" not in combined_output
