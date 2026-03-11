# -*- coding: utf-8 -*-
"""入口与项目脚本配置测试"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sync_workflow_uses_cli_sync_command():
    """同步工作流应通过 CLI 子命令触发同步"""
    content = (PROJECT_ROOT / ".github" / "workflows" / "sync.yml").read_text(
        encoding="utf-8"
    )
    assert "run: python main.py sync" in content


def test_cleanup_workflow_uses_cli_cleanup_command():
    """清理工作流应通过 CLI 子命令触发清理"""
    content = (PROJECT_ROOT / ".github" / "workflows" / "cleanup.yml").read_text(
        encoding="utf-8"
    )
    assert "run: python main.py cleanup" in content


def test_config_example_uses_cli_commands():
    """示例配置中的命令提示应与当前 CLI 一致"""
    content = (PROJECT_ROOT / "config.example.yaml").read_text(encoding="utf-8")
    assert "python3 main.py sync" in content
    assert "python3 main.py sync --full" in content
    assert "python3 main.py --full-sync" not in content
