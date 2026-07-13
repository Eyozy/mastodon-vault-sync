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


def test_menu_command_can_exit():
    """menu 子命令应打开交互菜单并允许退出"""
    result = subprocess.run(
        [sys.executable, "main.py", "menu"],
        cwd=PROJECT_ROOT,
        input="0\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "请选择要执行的操作" in result.stdout
    assert "已退出" in result.stdout


def test_no_args_opens_menu_and_can_exit():
    """无参数应默认打开交互菜单，降低本地使用记忆成本"""
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        input="0\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "请选择要执行的操作" in result.stdout
    assert "已退出" in result.stdout


def test_help_lists_menu_command():
    """帮助信息应展示交互式菜单入口"""
    result = run_cli("help")

    assert "menu" in result.stdout
    assert "打开交互式菜单" in result.stdout


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
