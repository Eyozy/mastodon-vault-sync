# -*- coding: utf-8 -*-
"""项目级文件与文档约束测试"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_requirements_excludes_dev_tools():
    """运行依赖文件不应混入测试和格式化工具"""
    content = read_text("requirements.txt")
    assert "pytest" not in content
    assert "pre-commit" not in content
    assert "black" not in content
    assert "isort" not in content
    assert "flake8" not in content


def test_dev_requirements_includes_runtime_and_dev_tools():
    """开发依赖文件应复用运行依赖并包含开发工具"""
    content = read_text("requirements-dev.txt")
    assert "-r requirements.txt" in content
    assert "pytest" in content
    assert "pre-commit" in content
    assert "black" in content
    assert "isort" in content
    assert "flake8" in content


def test_ci_workflow_exists_and_runs_quality_checks():
    """仓库应提供独立 CI workflow 执行检查和测试"""
    content = read_text(".github/workflows/ci.yml")
    assert "name: CI" in content
    assert "pre_commit" in content or "pre-commit" in content
    assert "pytest" in content


def test_issue_and_pr_templates_exist():
    """仓库应提供基础 PR 和 Issue 模板"""
    assert (PROJECT_ROOT / ".github" / "pull_request_template.md").exists()
    assert (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").exists()
    assert (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").exists()


def test_readme_documents_runtime_and_dev_installation():
    """README 应区分普通使用和开发安装"""
    content = read_text("README.md")
    assert "requirements-dev.txt" in content
    assert "python3 -m pytest tests/ -v" in content
    assert "py -m pytest tests/ -v" in content


def test_contributing_documents_dev_requirements_and_templates():
    """贡献文档应说明开发依赖安装和提交流程"""
    content = read_text("CONTRIBUTING.md")
    assert "requirements-dev.txt" in content
    assert "python3 -m pre_commit run --all-files" in content
    assert "python3 -m pytest tests/ -v" in content


def test_tests_readme_documents_dev_requirements():
    """测试文档应要求安装开发依赖"""
    content = read_text("tests/README.md")
    assert "requirements-dev.txt" in content
    assert "python3 -m pytest tests/ -v" in content
