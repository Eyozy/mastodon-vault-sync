# -*- coding: utf-8 -*-
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


def get_timezone_aware_datetime(
    created_at_str: str, china_timezone: bool = False
) -> datetime:
    """
    根据配置的时区设置转换时间字符串

    Args:
        created_at_str: ISO 格式的时间字符串
        china_timezone: 是否使用中国时区（GMT+8）

    Returns:
        转换后的带时区的 datetime 对象
    """
    dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc
    )

    if china_timezone:
        # 使用中国时区 (GMT+8)
        return dt.astimezone(timezone(timedelta(hours=8)))
    else:
        # 使用 UTC
        return dt


def parse_rate_limit_reset(reset_header: Optional[str]) -> Optional[int]:
    """解析 Mastodon API 的 X-RateLimit-Reset 时间戳"""
    if not reset_header:
        return None

    try:
        # 尝试解析为 Unix 时间戳（秒数）
        return int(reset_header)
    except ValueError:
        pass  # 继续尝试其他格式

    try:
        # 尝试解析为 ISO 格式时间戳
        if "T" in reset_header:
            # 移除微秒部分，避免解析问题
            clean_time = reset_header.split(".")[0] + (
                "Z" if reset_header.endswith("Z") else ""
            )
            if reset_header.endswith("Z"):
                reset_time = datetime.strptime(clean_time, "%Y-%m-%dT%H:%M:%SZ")
                reset_time = reset_time.replace(tzinfo=timezone.utc)
            else:
                reset_time = datetime.fromisoformat(clean_time)
            return int(reset_time.timestamp())
    except (ValueError, AttributeError):
        pass

    # 如果都失败了，返回 None，使用默认值
    return None


def get_color_from_count(count: int) -> str:
    if count == 0:
        return "#ebedf0"
    if 1 <= count <= 2:
        return "#9be9a8"
    if 3 <= count <= 5:
        return "#40c463"
    if 6 <= count <= 9:
        return "#30a14e"
    return "#216e39"


def safe_remove_directory(path: "Path") -> bool:  # type: ignore
    """
    安全删除目录，处理权限问题和文件锁定
    """
    if not path.exists():
        return True

    try:
        # 首先尝试正常删除
        shutil.rmtree(path)
        return True
    except PermissionError as e:
        logging.warning(f"⚠️ 权限错误，尝试强制删除目录 {path}: {e}")

        # 尝试移除只读属性
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.chmod(file_path, 0o777)
                    except (OSError, PermissionError):
                        pass
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        os.chmod(dir_path, 0o777)
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            logging.warning(f"⚠️ 移除只读属性失败：{e}")

        # 再次尝试删除
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            # 如果还是失败，尝试逐个删除文件
            try:
                import stat

                def remove_readonly(func, path, excinfo):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                shutil.rmtree(path, onerror=remove_readonly)
                return True
            except Exception as e:
                logging.error(f"❌ 无法删除目录 {path}: {e}")
                return False
    except Exception as e:
        logging.error(f"❌ 删除目录 {path} 时发生未知错误：{e}")
        return False


def safe_remove_file(path: "Path") -> bool:  # type: ignore
    """
    安全删除文件，处理权限问题
    """
    if not path.exists():
        return True

    try:
        path.unlink()
        return True
    except PermissionError as e:
        logging.warning(f"⚠️ 权限错误，尝试强制删除文件 {path}: {e}")
        try:
            # 尝试移除只读属性
            os.chmod(path, 0o777)
            path.unlink()
            return True
        except Exception as e:
            logging.error(f"❌ 无法删除文件 {path}: {e}")
            return False
    except Exception as e:
        logging.error(f"❌ 删除文件 {path} 时发生未知错误：{e}")
        return False
