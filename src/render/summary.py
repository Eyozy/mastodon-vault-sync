# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import yaml

from ..utils import get_color_from_count


def generate_heatmap_svg(
    post_counts: Dict[date, int],
    year: int,
    output_path: Path,
    username: str = "",
    instance: str = "",
) -> None:
    logging.info(f"🎨 正在为 {year} 年生成 SVG 热力图...")
    SQUARE_SIZE, SPACING = 10, 3
    SQUARE_TOTAL_SIZE = SQUARE_SIZE + SPACING
    X_OFFSET, Y_OFFSET = 25, 35
    WIDTH = X_OFFSET + SQUARE_TOTAL_SIZE * 53 + SPACING
    HEIGHT = Y_OFFSET + SQUARE_TOTAL_SIZE * 7 + 20

    # 计算嘟文总数
    total_posts = sum(post_counts.values())

    svg_parts = [
        f'<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">',
        (
            "<style>"
            ".month-label, .wday-label, .year-label, .total-label, .user-label { "
            'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, '
            '"Apple Color Emoji", "Segoe UI Emoji"; font-size: 9px; fill: #767676; } '
            ".year-label { font-size: 14px; font-weight: 600; } "
            ".total-label { font-size: 11px; font-weight: 500; } "
            ".user-label { font-size: 10px; }"
            "</style>"
        ),
    ]
    # 添加年份标签（左上角）
    svg_parts.append(f'<text x="0" y="15" class="year-label">{year}</text>')
    # 添加嘟文总数（右上角）
    svg_parts.append(
        f'<text x="{WIDTH - 5}" y="15" class="total-label" text-anchor="end">共 {total_posts} 条嘟文</text>'
    )
    # 添加用户信息（右下角）
    if username and instance:
        user_text = f"@{username}@{instance}"
        svg_parts.append(
            f'<text x="{WIDTH - 5}" y="{HEIGHT - 5}" class="user-label" text-anchor="end">{user_text}</text>'
        )
    for day, label in {1: "M", 3: "W", 5: "F"}.items():
        svg_parts.append(
            f'<text x="0" y="{Y_OFFSET + day * SQUARE_TOTAL_SIZE + SQUARE_SIZE}" class="wday-label">{label}</text>'
        )
    year_start, month_labels = date(year, 1, 1), {}
    year_start_weekday = (year_start.weekday() + 1) % 7
    days_in_year = (
        366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    )
    for day_of_year in range(days_in_year):
        current_date = year_start + timedelta(days=day_of_year)
        if current_date.year != year:
            continue
        if current_date.day == 1:  # 修复：移除 day_of_year > 0 条件，让 1 月也能显示
            month_labels[(day_of_year + year_start_weekday) // 7] = (
                current_date.strftime("%b")
            )
        count = post_counts.get(current_date, 0)
        total_days = day_of_year + year_start_weekday
        x_pos, y_pos = (
            X_OFFSET + (total_days // 7) * SQUARE_TOTAL_SIZE,
            Y_OFFSET + (total_days % 7) * SQUARE_TOTAL_SIZE,
        )
        tooltip = f"{current_date.strftime('%Y-%m-%d')}: {count} post{'s' if count != 1 else ''}"
        svg_parts.append(
            f'<rect x="{x_pos}" y="{y_pos}" width="{SQUARE_SIZE}" height="{SQUARE_SIZE}" '
            f'fill="{get_color_from_count(count)}" rx="2" ry="2">'
            f"<title>{tooltip}</title></rect>"
        )
    for week, month in month_labels.items():
        svg_parts.append(
            f'<text x="{X_OFFSET + week * SQUARE_TOTAL_SIZE}" y="{Y_OFFSET - 8}" class="month-label">{month}</text>'
        )
    svg_parts.append("</svg>")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    logging.info(f"✅ 热力图已成功生成至 '{output_path.name}'。")


def generate_activity_summary(config: Dict[str, Any], backup_path: Path) -> None:
    logging.info("📊 正在生成活动总结报告...")
    backup_config = config["backup"]
    posts_folder_path = backup_path / backup_config["posts_folder"]
    summary_filepath = backup_path / backup_config["summary_filename"]

    if not posts_folder_path.exists() or not any(posts_folder_path.iterdir()):
        logging.warning("⚠️ 未找到帖子备份文件夹或文件夹为空，无法生成总结报告。")
        return

    all_posts = []
    for post_file in sorted(list(posts_folder_path.glob("*.md")), reverse=True):
        try:
            with open(post_file, "r", encoding="utf-8") as f:
                content = f.read()
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            frontmatter = yaml.safe_load(parts[1])
            all_posts.append(
                {
                    "datetime": datetime.strptime(
                        frontmatter.get("date") or frontmatter.get("createdAt"),
                        "%Y-%m-%d %H:%M:%S",
                    ).date(),
                    "content": parts[2].strip().replace("../media/", "./media/"),
                    "source": frontmatter.get("source", ""),
                    "type": frontmatter.get("type", "toot"),
                }
            )
        except (OSError, yaml.YAMLError, ValueError, TypeError, KeyError) as e:
            logging.error(f"❌ 处理文件 {post_file.name} 时出错：{e}")

    if not all_posts:
        summary_filepath.write_text(
            "# Mastodon 活动存档\n\n未找到任何帖子来生成报告。", encoding="utf-8"
        )
        return

    # 获取用户信息
    username = config.get("username", "")
    instance = config.get("instance", "")

    # 如果 config 中没有用户信息，尝试从第一个帖子的 frontmatter source URL 中提取
    if (not username or not instance) and posts_folder_path.exists():
        try:
            first_post_file = sorted(list(posts_folder_path.glob("*.md")))[0]
            with open(first_post_file, "r", encoding="utf-8") as f:
                content = f.read()
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                source_url = frontmatter.get("source", "")
                # 从 source URL 提取：https://instance/@username/123456
                if source_url and "@" in source_url:
                    url_parts = (
                        source_url.split("//")[1] if "//" in source_url else source_url
                    )
                    instance = url_parts.split("/")[0]
                    username_part = (
                        url_parts.split("@")[1].split("/")[0]
                        if "@" in url_parts
                        else ""
                    )
                    username = username_part if username_part else username
        except (
            OSError,
            yaml.YAMLError,
            ValueError,
            TypeError,
            KeyError,
            IndexError,
        ) as e:
            logging.warning(f"无法从帖子中提取用户信息：{e}")

    # 按年份分组帖子
    posts_by_year = defaultdict(lambda: defaultdict(int))
    for post in all_posts:
        year = post["datetime"].year
        post_date = post["datetime"]
        posts_by_year[year][post_date] += 1

    # 获取所有年份并排序（从新到旧）
    all_years = sorted(posts_by_year.keys(), reverse=True)

    today = date.today()
    final_md = f"# Mastodon 活动存档\n\n> 最后更新：{today.strftime('%Y-%m-%d')}\n\n"

    # 为每个年份生成热力图
    for year in all_years:
        heatmap_svg_filename = f"heatmap-{year}.svg"
        heatmap_svg_filepath = backup_path / heatmap_svg_filename

        # 生成该年份的热力图
        generate_heatmap_svg(
            posts_by_year[year], year, heatmap_svg_filepath, username, instance
        )

        # 计算该年份的总嘟文数
        total_posts_this_year = sum(posts_by_year[year].values())

        # 添加到 Markdown
        final_md += (
            f"## {year} 年活动热力图\n\n"
            f"本年度共发布 {total_posts_this_year} 篇嘟文。\n\n"
            f"![{year} Activity Heatmap](./{heatmap_svg_filename})\n\n"
        )

    summary_filepath.write_text(final_md, encoding="utf-8")
    logging.info(f"✅ 活动总结报告已成功更新至 '{summary_filepath.name}'。")
    logging.info(f"✅ 共生成 {len(all_years)} 个年份的热力图。")
