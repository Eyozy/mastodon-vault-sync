# 测试说明

本项目使用 pytest 进行测试，确保核心功能稳定可靠。

## 环境准备

### 1. 创建并激活虚拟环境

```bash
# macOS / Linux: 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate
```

```powershell
# Windows: 创建并激活虚拟环境
py -m venv venv
venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` 会自动包含运行依赖，并安装 `pytest`、`pre-commit`、`black`、`isort`、`flake8` 等开发工具。

## 运行测试

```bash
# 确保在项目根目录下(包含 tests/ 和 src/ 目录)
pwd  # 应该显示 .../mastodon-vault-sync
```

```bash
# macOS / Linux: 运行所有测试
python3 -m pytest tests/ -v

# macOS / Linux: 显示详细输出(包括 print 语句)
python3 -m pytest tests/ -v -s

# macOS / Linux: 仅运行流程级 smoke tests
python3 -m pytest tests/test_sync_flow.py tests/test_cleanup_flow.py -v
```

```powershell
# Windows: 运行所有测试
py -m pytest tests/ -v

# Windows: 显示详细输出(包括 print 语句)
py -m pytest tests/ -v -s

# Windows: 仅运行流程级 smoke tests
py -m pytest tests/test_sync_flow.py tests/test_cleanup_flow.py -v
```

如果你的 Windows 环境没有 `py` 命令，可以改用 `python -m pytest ...`。

## 测试覆盖

当前测试覆盖：
- ✅ 配置验证（有效配置、缺少字段、无效 URL）
- ✅ 配置结构完整性检查
- ✅ `sync_state.json` 与 GitHub Actions 增量同步约束
- ✅ 归档重建、HTML 输出安全和 CLI 入口行为
- ✅ 端到端同步流程与 cleanup 流程 smoke tests

## 关于 `sync_state.json`

- `sync_state.json` 是增量同步的状态文件，项目默认需要跟踪它
- 如果你只是在本地跑测试或调试，不想提交这个文件，请使用 `.git/info/exclude`
- 不要把它重新写进项目级 `.gitignore`

## 贡献者指南

### 添加新测试

1. 在 `tests/` 目录下创建 `test_*.py` 文件
2. 使用 `conftest.py` 中的 fixtures（如 `sample_config`）
3. 运行测试确保通过

### 测试命名规范

- 测试文件：`test_*.py`
- 测试函数：`test_*`
- 测试类：`Test*`

### 示例

```python
def test_my_feature(sample_config):
    """测试描述"""
    # 测试代码
    assert result == expected
```

## 常见问题

### pytest: command not found 或 no such file or directory

**最可能的原因**：你不在项目根目录下

**解决方案**：

1. 检查当前目录
```bash
pwd
# 应该显示类似：/Users/xxx/.../mastodon-vault-sync
```

2. 检查 venv 是否存在
```bash
ls -la venv/
# 应该能看到 bin、lib 等目录
```

3. 如果不在正确目录，切换到项目根目录
```bash
cd /path/to/mastodon-vault-sync
```

### ModuleNotFoundError: No module named 'src'

**原因**：使用了 `pytest tests/ -v` 这类裸命令，当前项目结构下 Python 没有稳定拿到项目根目录

**推荐解决**：
```bash
python3 -m pytest tests/ -v
```

```powershell
py -m pytest tests/ -v
```

**备用解决**：
```bash
PYTHONPATH=. pytest tests/ -v
```
