# -*- coding: utf-8 -*-
import re

CSS_STYLES = """
:root {
    --bg-color: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-tertiary: #f1f5f9;
    --bg-card: #ffffff;
    --bg-hover: #f8fafc;
    --bg-search: #f1f5f9;

    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --text-link: #6364ff;

    --accent-color: #6364ff;
    --accent-hover: #5858d6;
    --accent-light: #e8e7ff;
    --accent-gradient: linear-gradient(135deg, #6364ff 0%, #8b5cf6 100%);

    --border-color: #e2e8f0;
    --border-light: #f1f5f9;
    --border-focus: #6364ff;

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-full: 9999px;

    --transition-fast: 0.15s ease;
    --transition-base: 0.3s ease;
    --transition-slow: 0.5s ease;
}

[data-theme="dark"] {
    --bg-color: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --bg-hover: #334155;
    --bg-search: #334155;

    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --text-link: #a78bfa;

    --accent-color: #818cf8;
    --accent-hover: #6366f1;
    --accent-light: #1e3a8a;
    --accent-gradient: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);

    --border-color: #334155;
    --border-light: #475569;
    --border-focus: #818cf8;

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
    transition: background-color 0.3s ease, color 0.3s ease;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

h1, .h1 {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

h2, .h2 {
    font-size: 1.5rem;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

h3, .h3 {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

h4, .h4 {
    font-size: 1.125rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.text-xs {
    font-size: 0.75rem;
    font-weight: 400;
    line-height: 1.4;
    color: var(--text-muted);
}

.text-sm {
    font-size: 0.875rem;
    font-weight: 400;
    line-height: 1.5;
    color: var(--text-secondary);
}

.text-base {
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.6;
    color: var(--text-primary);
}

.text-lg {
    font-size: 1.125rem;
    font-weight: 400;
    line-height: 1.7;
    color: var(--text-primary);
}

.font-bold {
    font-weight: 700;
}

.font-semibold {
    font-weight: 600;
}

.font-medium {
    font-weight: 500;
}

.font-normal {
    font-weight: 400;
}

.text-primary {
    color: var(--text-primary);
}

.text-secondary {
    color: var(--text-secondary);
}

.text-muted {
    color: var(--text-muted);
}

.text-link {
    color: var(--text-link);
    text-decoration: none;
    transition: color var(--transition-fast);
}

.text-link:hover {
    color: var(--accent-hover);
    text-decoration: underline;
}

.header {
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
}

.header-content {
    width: 600px;
    max-width: 100%;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 0;
}

.search-container {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
}

.search-input {
    flex: 1;
    padding: 0.75rem 3.5rem 0.75rem 2.5rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background-color: var(--bg-search);
    color: var(--text-primary);
    font-size: 1rem;
    transition: border-color 0.2s ease;
}

.search-input:focus {
    outline: none;
    border-color: var(--accent-color);
    background-color: var(--bg-card);
    box-shadow: 0 0 0 3px var(--accent-light);
}

.search-icon {
    position: absolute;
    left: 0.75rem;
    color: var(--text-muted);
    pointer-events: none;
    width: 16px;
    height: 16px;
}

.clear-btn {
    color: var(--text-muted);
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
    padding: 0.4rem;
    border-radius: var(--radius-full);
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    display: none;
    transition: all var(--transition-fast);
    width: 28px;
    height: 28px;
    z-index: 10;
}

.clear-btn:hover {
    color: var(--text-primary);
    background-color: var(--bg-hover);
    border-color: var(--border-color);
}

.clear-btn.show {
    display: flex;
    align-items: center;
    justify-content: center;
}

.clear-btn svg {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}

.theme-toggle {
    background: var(--bg-search);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all var(--transition-base);
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.theme-toggle:hover {
    background-color: var(--bg-hover);
    border-color: var(--accent-color);
    transform: rotate(15deg);
}

.theme-toggle:focus {
    outline: none;
    border-color: var(--accent-color);
}

.theme-toggle svg {
    width: 18px;
    height: 18px;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
    margin: 2rem 0;
    padding: 1rem 0;
}

.pagination-info {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0 1rem;
}

.pagination-btn {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.75rem 1.25rem;
    border-radius: var(--radius-md);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all var(--transition-base);
    font-weight: 500;
}

.pagination-btn:hover:not(:disabled) {
    background-color: var(--bg-hover);
    border-color: var(--accent-color);
    color: var(--accent-color);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.pagination-btn:active:not(:disabled) {
    transform: translateY(0);
}

.pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.pagination-btn svg {
    width: 16px;
    height: 16px;
}

.pagination-current {
    background-color: var(--accent-color);
    color: white;
    border-color: var(--accent-color);
}

.container {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem 0rem;
}

.section-mb-1 { margin-bottom: 0.5rem; }
.section-mb-2 { margin-bottom: 1rem; }
.section-mb-3 { margin-bottom: 1.5rem; }
.section-mb-4 { margin-bottom: 2rem; }
.section-mb-5 { margin-bottom: 2.5rem; }
.section-mb-6 { margin-bottom: 3rem; }

.content-padding {
    padding: 0 1rem;
}

.card {
    background-color: var(--bg-card);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    transition: box-shadow var(--transition-base);
}

.card:hover {
    box-shadow: var(--shadow-lg);
}

.user-profile {
    background-color: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: 0;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    overflow: hidden;
    width: 100%;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    transition: box-shadow var(--transition-base);
}

.user-profile:hover {
    box-shadow: var(--shadow-lg);
}

.profile-header {
    height: 160px;
    position: relative;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.profile-header.no-background {
    background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
}

.profile-info {
    position: relative;
    padding: 0 1rem 1.5rem;
    margin-top: -60px;
}

.user-avatar {
    width: 120px;
    height: 120px;
    border-radius: var(--radius-md);
    border: 4px solid var(--bg-card);
    background-color: var(--bg-card);
    box-shadow: var(--shadow-lg);
    transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.user-avatar:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-xl);
}

.profile-text {
    text-align: left;
    margin-top: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.user-name {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    color: var(--text-primary);
    line-height: 1.2;
}

.user-handle {
    color: var(--text-secondary);
    font-size: 1rem;
    margin-bottom: 1rem;
}

.user-stats {
    display: flex;
    gap: 1rem;
    padding-top: 1rem;
    width: fit-content;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex: none;
    text-align: center;
    min-width: 60px;
}

.stat-number {
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--text-primary);
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
}

.status {
    background-color: var(--bg-card);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease;
    width: 100%;
    border: 1px solid var(--border-color);
    margin-bottom: 1rem;
}

.status.hidden {
    display: none;
}

.status-reply {
    background-color: var(--bg-card);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: none;
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-left: 4px solid var(--accent-color);
}

.status-quote {
    background-color: var(--bg-card);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: none;
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-left: 4px solid var(--warning-color);
}

.status-header {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
    align-items: center;
}

.status-avatar {
    width: 46px;
    height: 46px;
    border-radius: 12%;
    flex-shrink: 0;
    object-fit: cover;
}

.status-meta {
    flex: 1;
    min-width: 0;
    display: block;
}

.status-name {
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.95rem;
    line-height: 1.3;
    display: block;
}

.status-name:hover {
    text-decoration: underline;
}

.status-handle {
    color: var(--text-secondary);
    font-size: 0.85rem;
    line-height: 1.3;
    display: block;
    margin-top: 0.15rem;
}

.status-time {
    color: var(--text-muted);
    font-size: 0.8rem;
    white-space: nowrap;
    margin-left: auto;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.status-full-date {
    font-size: 0.9rem;
    font-weight: 600;
    line-height: 1;
}

.status-time-detail {
    font-size: 0.75rem;
    line-height: 1.2;
    margin-top: 2px;
}

.status-content {
    margin-bottom: 1rem;
    line-height: 1.6;
}

/* 为所有帖子图片添加点击查看大图功能 */
.status-content > img,
.media-gallery img.media-item {
    display: block !important;
    cursor: pointer !important;
    transition: transform 0.2s ease !important;
}

.status-content > img:hover {
    transform: scale(1.02) !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
}

/* 图片模态框样式 */
#imageModal {
    display: none;
    position: fixed;
    z-index: 9999;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0, 0, 0, 0.9);
}

#imageModal .modal-content {
    margin: auto;
    display: block;
    max-width: 90%;
    max-height: 90%;
    /* 完全居中 */
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transform-origin: center; /* 确保缩放从中心开始 */
    will-change: transform; /* 提升动画性能 */
    image-rendering: crisp-edges; /* 优化图片渲染 */
}

#imageModal #caption {
    margin: auto;
    display: block;
    width: 80%;
    max-width: 700px;
    text-align: center;
    color: #ccc;
    padding: 10px 0;
    height: 150px;
}

#imageModal .modal-content,
#imageModal #caption {
    animation-name: zoom;
    animation-duration: 0.6s;
}

@keyframes zoom {
    from {
        transform: translate(-50%, -50%) scale(0); /* 保持居中 */
        opacity: 0;
    }
    to {
        transform: translate(-50%, -50%) scale(1); /* 保持居中 */
        opacity: 1;
    }
}

#imageModal .close {
    position: absolute;
    top: 15px;
    right: 35px;
    color: #f1f1f1;
    font-size: 40px;
    font-weight: bold;
    transition: 0.3s;
}

#imageModal .close:hover,
#imageModal .close:focus {
    color: #bbb;
    text-decoration: none;
    cursor: pointer;
}

.status-content p {
    margin-bottom: 1rem;
}

.status-content p:last-child {
    margin-bottom: 0;
}

.status-content a {
    color: var(--accent-color);
    text-decoration: none;
    position: relative;
    transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}

.status-content a::after {
    content: '';
    position: absolute;
    width: 0;
    height: 2px;
    bottom: -2px;
    left: 0;
    background-color: var(--accent-color);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-content a:hover {
    color: var(--accent-hover);
}

.status-content a:hover::after {
    width: 100%;
}

.media-gallery {
    display: grid;
    gap: 0.5rem;
    margin: 1rem 0;
    border-radius: 8px;
    overflow: hidden;
}

.media-gallery.single {
    max-width: 100%;
}

.media-gallery.double {
    grid-template-columns: 1fr 1fr;
}

.media-gallery.multiple {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.media-item {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 8px;
}

.status-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.status-stats {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.stat-icon {
    width: 14px;
    height: 14px;
    opacity: 0.7;
}

.status-link {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    white-space: nowrap;
    flex-shrink: 0;
    position: relative;
    transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-link::after {
    content: '';
    position: absolute;
    width: 0;
    height: 1px;
    bottom: -1px;
    left: 0;
    background-color: var(--text-secondary);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-link:hover {
    color: var(--text-primary);
}

.status-link:hover::after {
    width: 100%;
}

.hashtag {
    color: var(--accent-color);
    text-decoration: none !important;  /* 确保覆盖原始内容中的样式 */
    transition: border-bottom-color 0.2s ease;
}

.hashtag:hover {
    text-decoration: none !important;  /* 确保没有默认下划线 */
    border-bottom: 1px solid var(--accent-color);  /* 使用底部边框作为下划线 */
}

.custom-emoji {
    width: 1.2em;
    height: 1.2em;
    vertical-align: middle;
    margin: 0 0.05em;
    object-fit: contain;
    border-radius: 3px;
    transition: transform 0.2s ease;
}

.custom-emoji:hover {
    transform: scale(1.1);
}

.no-results {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
}

html {
    scroll-behavior: smooth;
}

.back-to-top {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 48px;
    height: 48px;
    background-color: white;
    color: black;
    border: 1px solid #e0e0e0;
    border-radius: var(--radius-full);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-md);
    transition: all var(--transition-base);
    opacity: 0;
    visibility: hidden;
    z-index: 1000;
}

.back-to-top.show {
    opacity: 1;
    visibility: visible;
}

.back-to-top:hover {
    background-color: #f5f5f5;
    border-color: var(--accent-color);
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.back-to-top:focus-visible {
    outline: 2px solid var(--accent-color);
    outline-offset: 2px;
}

[data-theme="dark"] .back-to-top {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

[data-theme="dark"] .back-to-top:hover {
    background-color: var(--bg-hover);
}

.back-to-top svg {
    width: 20px;
    height: 20px;
}

*:focus-visible {
    outline: 2px solid var(--accent-color);
    outline-offset: 2px;
}

button:focus-visible,
input:focus-visible {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(99, 100, 255, 0.1);
}

@media (min-width: 1200px) {
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 0;
    }

    .header-content {
        padding: 1rem 0;
        max-width: 800px;
        margin: 0 auto;
    }

  }

@media (max-width: 1199px) and (min-width: 769px) {
    .container {
        max-width: 90%;
        padding: 1.5rem 1rem;
    }

    .search-input {
        width: 300px;
    }
}

@media (max-width: 768px) {
    .header-content {
        padding: 1rem 0.5rem;
    }

    .container {
        padding: 1rem 20px;
    }

    .profile-info {
        padding: 0 0.75rem 1.5rem;
    }

    .user-avatar {
        width: 100px;
        height: 100px;
        border-width: 3px;
    }

    .profile-header {
        height: 120px;
    }

    .user-name {
        font-size: 1.25rem;
    }

    .user-stats {
        gap: 1rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
    }

    .stat-number {
        font-size: 1rem;
    }

    .status-avatar {
        width: 40px;
        height: 40px;
    }

    .status-header {
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .status-content {
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .media-gallery.multiple {
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.25rem;
    }

    .media-item {
        border-radius: 6px;
    }

    .status-footer {
        flex-wrap: wrap;
        gap: 0.75rem;
        padding-top: 0.75rem;
    }

    .status-stats {
        flex-wrap: wrap;
        gap: 0.75rem;
    }

    .stat-icon {
        width: 12px;
        height: 12px;
    }

    .search-input {
        font-size: 16px;
        padding: 0.75rem 3rem 0.75rem 2.5rem;
    }

    .clear-btn {
        width: 20px;
        height: 20px;
        right: 0.5rem;
    }

    .clear-btn svg {
        width: 12px;
        height: 12px;
    }

    .theme-toggle {
        width: 36px;
        height: 36px;
        padding: 0.6rem;
    }

    .theme-toggle svg {
        width: 16px;
        height: 16px;
    }

    .pagination {
        margin: 1.5rem 0;
        padding: 0.75rem 0;
        gap: 0.375rem;
    }

    .pagination-btn {
        padding: 0.5rem 0.75rem;
        font-size: 0.85rem;
        min-height: 36px;
    }

    .pagination-info {
        font-size: 0.85rem;
        margin: 0 0.75rem;
    }

    .back-to-top {
        bottom: 1rem;
        right: 1rem;
        width: 44px;
        height: 44px;
    }
}

@media (max-width: 400px) {
    .header-content {
        width: 100%;
        padding: 0.75rem 0.5rem;
        gap: 0.5rem;
    }

    .container {
        width: 100%;
        padding: 1rem 0.5rem;
    }

    .user-profile {
        width: 100%;
        margin: 0 0 1.5rem 0;
    }

    .timeline {
        width: 100%;
        max-width: 100%;
        margin: 0;
        padding: 0;
    }

    body {
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
}

@media (max-width: 480px) {
    .search-input {
        width: 160px;
        font-size: 14px;
        padding: 0.6rem 2.8rem 0.6rem 2rem;
    }

    .search-icon {
        left: 0.6rem;
    }

    .theme-toggle {
        width: 36px;
        height: 36px;
        padding: 0.6rem;
    }

    .profile-info {
        padding: 0 0.5rem 1rem;
    }

    .user-avatar {
        width: 80px;
        height: 80px;
        border-width: 2px;
    }

    .profile-header {
        height: 100px;
    }

    .user-name {
        font-size: 1.125rem;
    }

    .user-handle {
        font-size: 0.9rem;
    }

    .user-stats {
        gap: 0.75rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
    }

    .stat-number {
        font-size: 0.95rem;
    }

    .stat-label {
        font-size: 0.7rem;
    }

    .status {
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.75rem;
    }

    .status-avatar {
        width: 36px;
        height: 36px;
    }

    .status-header {
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .status-content {
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .status-link {
        font-size: 0.8rem;
        padding: 4px 8px;
    }

    .media-gallery.multiple {
        grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
        gap: 0.25rem;
    }

    .status-footer {
        flex-direction: row;
        justify-content: space-between;
    }

    .status-link {
        align-self: center;
    }

    .pagination {
        flex-direction: column;
        gap: 0.75rem;
        margin: 1rem 0;
        padding: 0.75rem 0;
    }

    .pagination-btn {
        padding: 0.5rem 0.75rem;
        font-size: 0.85rem;
        min-height: 36px;
    }

    .pagination-info {
        font-size: 0.85rem;
        margin: 0;
    }

    .back-to-top {
        bottom: 1rem;
        right: 1rem;
        width: 44px;
        height: 44px;
    }

    .back-to-top svg {
        width: 16px;
        height: 16px;
    }
}

@media (max-width: 360px) {
    .header-content {
        padding: 0.5rem 0.25rem;
    }

    .container {
        padding: 0.75rem 0.5rem;
    }

    .search-input {
        width: 120px;
        font-size: 13px;
        padding: 0.5rem 2.5rem 0.5rem 2rem;
    }

    .theme-toggle {
        width: 32px;
        height: 32px;
        padding: 0.5rem;
    }

    .theme-toggle svg {
        width: 14px;
        height: 14px;
    }

    .profile-info {
        padding: 0 0.25rem 0.75rem;
    }

    .user-avatar {
        width: 70px;
        height: 70px;
        border-width: 2px;
    }

    .user-name {
        font-size: 1rem;
    }

    .user-handle {
        font-size: 0.85rem;
    }

    .user-stats {
        gap: 0.5rem;
    }

    .stat-number {
        font-size: 0.85rem;
    }

    .stat-label {
        font-size: 0.65rem;
    }

    .status {
        padding: 0.6rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }

    .status-avatar {
        width: 32px;
        height: 32px;
    }

    .status-content {
        font-size: 0.85rem;
    }

    .status-link {
        font-size: 0.75rem;
        padding: 3px 6px;
    }

    .status-link::before {
        font-size: 0.8em;
        margin-right: 4px;
    }

    .pagination {
        gap: 0.5rem;
    }

    .pagination-btn {
        padding: 0.4rem 0.6rem;
        font-size: 0.8rem;
        min-height: 32px;
    }

    .back-to-top {
        bottom: 0.75rem;
        right: 0.75rem;
        width: 40px;
        height: 40px;
    }
}

@media (max-height: 500px) and (orientation: landscape) {
    .profile-header {
        height: 120px;
    }

    .user-avatar {
        width: 90px;
        height: 90px;
    }

    .profile-info {
        margin-top: -45px;
    }

  
    .status-content {
        font-size: 0.95rem;
    }

    .user-stats {
        margin-top: 0.5rem;
        padding-top: 0.5rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
        --bg-color: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --bg-card: #1e293b;
        --bg-hover: #334155;
        --bg-search: #334155;

        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --text-link: #a78bfa;

        --accent-color: #818cf8;
        --accent-hover: #6366f1;
        --accent-light: #1e3a8a;
        --accent-gradient: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);

        --border-color: #334155;
        --border-light: #475569;
        --border-focus: #818cf8;

        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
    }
}

@media (prefers-contrast: high) {
    :root {
        --border-color: #000000;
        --text-secondary: #000000;
        --shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }

    [data-theme="dark"] {
        --border-color: #ffffff;
        --text-secondary: #ffffff;
        --shadow: 0 2px 4px rgba(255, 255, 255, 0.1);
    }
}

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--text-muted);
    border-radius: var(--radius-full);
    transition: background-color var(--transition-fast);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}
"""

JAVASCRIPT_CODE = """
const POSTS_PER_PAGE = 40;
let currentPage = 1;
let currentPosts = [];
let filteredPosts = [];

document.addEventListener('DOMContentLoaded', function() {
    postsData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    currentPosts = [...postsData];
    filteredPosts = [...currentPosts];

    renderCurrentPage();
    setupSearch();
    setupThemeToggle();
    setupPagination();
    setupImageModal();
});

function renderCurrentPage() {
    const timeline = document.getElementById('timeline');
    const noResults = document.getElementById('noResults');

    if (filteredPosts.length === 0) {
        timeline.innerHTML = '';
        noResults.style.display = 'block';
        updatePaginationUI();
        return;
    }

    noResults.style.display = 'none';
    const startIndex = (currentPage - 1) * POSTS_PER_PAGE;
    const endIndex = startIndex + POSTS_PER_PAGE;
    const postsToShow = filteredPosts.slice(startIndex, endIndex);

    timeline.innerHTML = postsToShow.map(post => createPostHTML(post)).join('');
    updatePaginationUI();

    // 重新绑定图片点击事件
    setupImageModal();
}

function renderPosts(posts) {
    currentPosts = [...posts].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    filteredPosts = [...currentPosts];
    currentPage = 1;
    renderCurrentPage();
}

function updatePaginationUI() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const pageInfo = document.getElementById('pageInfo');
    const pagination = document.getElementById('pagination');

    const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);

    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }

    pagination.style.display = 'flex';
    pageInfo.textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
}

function setupPagination() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    prevBtn.addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            renderCurrentPage();
            window.scrollTo(0, 0);
        }
    });

    nextBtn.addEventListener('click', function() {
        const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);
        if (currentPage < totalPages) {
            currentPage++;
            renderCurrentPage();
            window.scrollTo(0, 0);
        }
    });

    document.addEventListener('keydown', function(e) {
        const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);
        if (e.key === 'ArrowLeft' && currentPage > 1) {
            currentPage--;
            renderCurrentPage();
            window.scrollTo(0, 0);
        } else if (e.key === 'ArrowRight' && currentPage < totalPages) {
            currentPage++;
            renderCurrentPage();
            window.scrollTo(0, 0);
        }
    });
}

function createPostHTML(post) {
    const mediaHTML = createMediaHTML(post.media_attachments);
    const tagsHTML = post.tags.map(tag => `<a href="#" class="hashtag">#${tag.name}</a>`).join(' ');
    const statsHTML = `
        <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            ${post.replies_count}
        </span>
        <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon">
                <polyline points="17 1 21 5 17 9"/>
                <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
                <polyline points="7 23 3 19 7 15"/>
                <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
            </svg>
            ${post.reblogs_count}
        </span>
        <span class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            ${post.favourites_count}
        </span>
    `;

    const isReply = post.in_reply_to_id && post.in_reply_to_id !== null;
    const hasRELink = post.content && (
        post.content.includes('RE:') ||
        post.content.includes('re:') ||
        post.content.includes('Re:') ||
        post.content.toLowerCase().includes('re:')
    );
    const isQuote = hasRELink && !isReply;

    if (isReply) {
        return `
            <div class="status-reply" data-id="${post.id}">
                <div class="status-header">
                    <img src="${post.account.avatar}" alt="${post.account.display_name}" class="status-avatar" onerror="this.style.display='none'">
                    <div class="status-meta">
                        <a href="${post.account.url}" class="status-name" target="_blank">${post.account.display_name}</a>
                        <div class="status-handle">@${post.account.username}</div>
                    </div>
                    <div class="status-time">
                        <div class="status-full-date">${post.created_at.split(' ')[0]}</div>
                        <div class="status-time-detail">${post.created_at.split(' ')[1].split(':')[0]}:${post.created_at.split(' ')[1].split(':')[1]}</div>
                    </div>
                </div>
                <div class="status-content">
                    ${post.content}
                </div>
                ${mediaHTML}
                <div class="status-footer">
                    <div class="status-stats">
                        ${statsHTML}
                    </div>
                    <a href="${post.url}" class="status-link" target="_blank">查看回复</a>
                </div>
            </div>
        `;
    } else if (isQuote) {
        return `
            <div class="status-quote" data-id="${post.id}">
                <div class="status-header">
                    <img src="${post.account.avatar}" alt="${post.account.display_name}" class="status-avatar" onerror="this.style.display='none'">
                    <div class="status-meta">
                        <a href="${post.account.url}" class="status-name" target="_blank">${post.account.display_name}</a>
                        <div class="status-handle">@${post.account.username}</div>
                    </div>
                    <div class="status-time">
                        <div class="status-full-date">${post.created_at.split(' ')[0]}</div>
                        <div class="status-time-detail">${post.created_at.split(' ')[1].split(':')[0]}:${post.created_at.split(' ')[1].split(':')[1]}</div>
                    </div>
                </div>
                <div class="status-content">
                    ${post.content}
                </div>
                ${mediaHTML}
                <div class="status-footer">
                    <div class="status-stats">
                        ${statsHTML}
                    </div>
                    <a href="${post.url}" class="status-link" target="_blank">查看引用</a>
                </div>
            </div>
        `;
    } else {
        return `
            <div class="status" data-id="${post.id}">
                <div class="status-header">
                    <img src="${post.account.avatar}" alt="${post.account.display_name}" class="status-avatar" onerror="this.style.display='none'">
                    <div class="status-meta">
                        <a href="${post.account.url}" class="status-name" target="_blank">${post.account.display_name}</a>
                        <div class="status-handle">@${post.account.username}</div>
                    </div>
                    <div class="status-time">
                        <div class="status-full-date">${post.created_at.split(' ')[0]}</div>
                        <div class="status-time-detail">${post.created_at.split(' ')[1].split(':')[0]}:${post.created_at.split(' ')[1].split(':')[1]}</div>
                    </div>
                </div>
                <div class="status-content">
                    ${post.content}
                </div>
                ${mediaHTML}
                <div class="status-footer">
                    <div class="status-stats">
                        ${statsHTML}
                    </div>
                    <a href="${post.url}" class="status-link" target="_blank">查看原文</a>
                </div>
            </div>
        `;
    }
}

function createMediaHTML(mediaAttachments) {
    if (!mediaAttachments || mediaAttachments.length === 0) return '';

    const mediaCount = mediaAttachments.length;
    let galleryClass = 'single';
    if (mediaCount === 2) galleryClass = 'double';
    else if (mediaCount > 2) galleryClass = 'multiple';

    const mediaItems = mediaAttachments.map(media => `
        <img src="${media.url}"
             alt="${media.description || 'Media'}"
             class="media-item"
             loading="lazy">
    `).join('');

    return `<div class="media-gallery ${galleryClass}">${mediaItems}</div>`;
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearBtn');

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        clearBtn.classList.toggle('show', query.length > 0);

        const filteredPosts = query
            ? filterPosts(postsData, query)
            : postsData;

        renderPosts(filteredPosts);
    });

    clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        this.classList.remove('show');
        renderPosts(postsData);
        searchInput.focus();
    });

    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            this.value = '';
            clearBtn.classList.remove('show');
            renderPosts(postsData);
        }
    });
}

function filterPosts(posts, query) {
    const lowerQuery = query.toLowerCase();
    return posts.filter(post =>
        post.content.toLowerCase().includes(lowerQuery) ||
        post.account.display_name.toLowerCase().includes(lowerQuery) ||
        post.account.username.toLowerCase().includes(lowerQuery) ||
        post.tags.some(tag => tag.name.toLowerCase().includes(lowerQuery))
    );
}

function setupThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    html.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    themeToggle.addEventListener('click', function() {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('.theme-icon');

    if (theme === 'light') {
        themeIcon.innerHTML = `
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        `;
    } else {
        themeIcon.innerHTML = `
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        `;
    }
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    const savedTheme = localStorage.getItem('theme');
    if (!savedTheme) {
        const newTheme = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        updateThemeIcon(newTheme);
    }
});

// 图片点击放大功能
let modalInitialized = false;

function setupImageModal() {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const captionText = document.getElementById('caption');

    // 为所有帖子图片添加点击事件
    const images = document.querySelectorAll('.status-content > img, .media-gallery img.media-item');

    images.forEach(img => {
        img.addEventListener('click', function() {
            modal.style.display = 'block';
            modalImg.src = this.src;
            modalImg.alt = this.alt;
            captionText.innerHTML = this.alt;
        });
    });

    // 只初始化一次事件监听器
    if (!modalInitialized) {
        // 点击关闭按钮
        const closeBtn = document.querySelector('#imageModal .close');
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };

        // 点击模态框背景关闭
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };

        // 按 ESC 键关闭
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });

        modalInitialized = true;
    }
}

const backToTopBtn = document.createElement('button');
backToTopBtn.className = 'back-to-top';
backToTopBtn.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="18 15 12 9 6 15"/>
    </svg>
`;
backToTopBtn.title = '回到顶部';
backToTopBtn.setAttribute('aria-label', '回到顶部');
backToTopBtn.type = 'button';
document.body.appendChild(backToTopBtn);

window.addEventListener('scroll', function() {
    if (window.pageYOffset > 300) {
        backToTopBtn.classList.add('show');
    } else {
        backToTopBtn.classList.remove('show');
    }
});

backToTopBtn.addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Home' && !e.target.matches('input, textarea, select')) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
});

"""


def get_html_body_template(
    username,
    display_name,
    avatar,
    instance_name,
    background_image,
    total_posts,
    followers_count,
    following_count,
):
    """生成 HTML body 内容（带用户数据）"""
    # 处理背景图片
    bg_style = (
        f' style="background-image: url({background_image})"'
        if background_image
        else ""
    )

    return f"""<!-- 图片放大模态框 -->
<div id="imageModal" class="modal">
    <span class="close">&times;</span>
    <img class="modal-content" id="modalImage">
    <div id="caption"></div>
</div>

<header class="header">
    <div class="header-content">
        <div class="search-container">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
            </svg>
            <input type="text" class="search-input" placeholder="搜索嘟文..." id="searchInput" aria-label="搜索嘟文" autocomplete="off" spellcheck="false">
            <button class="clear-btn" id="clearBtn" title="清空搜索" aria-label="清空搜索内容" type="button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18"/>
                    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                </svg>
            </button>
        </div>
        <button class="theme-toggle" id="themeToggle" title="切换主题" aria-label="切换明暗主题" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
        </button>
    </div>
</header>

<main class="container">
    <div class="user-profile">
        <div class="profile-header"{bg_style}></div>
        <div class="profile-info">
            <img src="{avatar}" alt="{display_name}" class="user-avatar" onerror="this.style.display='none'">
            <div class="profile-text">
                <h1 class="user-name">{display_name}</h1>
                <div class="user-handle">@{username}@{instance_name}</div>
            </div>
            <div class="user-stats">
                <div class="stat-item">
                    <span class="stat-number">{total_posts}</span>
                    <span class="stat-label">嘟文</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{following_count}</span>
                    <span class="stat-label">关注中</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{followers_count}</span>
                    <span class="stat-label">关注者</span>
                </div>
            </div>
        </div>
    </div>

    <div class="timeline" id="timeline">
        <!-- Posts will be inserted here by JavaScript -->
    </div>

    <div class="pagination" id="pagination">
        <button class="pagination-btn" id="prevBtn" title="上一页" aria-label="上一页" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="15 18 9 12 15 6"/>
            </svg>
            上一页
        </button>
        <span class="pagination-info" id="pageInfo" aria-live="polite" aria-atomic="true">第 1 页，共 1 页</span>
        <button class="pagination-btn" id="nextBtn" title="下一页" aria-label="下一页" type="button">
            下一页
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6"/>
            </svg>
        </button>
    </div>

    <div class="no-results" id="noResults" style="display: none;">
        <p>没有找到匹配的嘟文</p>
    </div>
</main>
"""


def generate_html(
    username,
    display_name,
    avatar,
    instance_name,
    background_image,  # 用于页面背景的本地路径
    og_image_url,       # 用于 OpenGraph 的完整 URL
    total_posts,
    followers_count,
    following_count,
    posts_json,
    user_bio,
):
    """生成完整的 HTML 页面"""

    # 生成 HTML body（包含用户数据）
    html_body = get_html_body_template(
        username=username,
        display_name=display_name,
        avatar=avatar,
        instance_name=instance_name,
        background_image=background_image,
        total_posts=total_posts,
        followers_count=followers_count,
        following_count=following_count,
    )

    # 组装完整 HTML
    html_output = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{username}的 Mastodon 备份</title>
    <meta name="description" content="{re.sub(r'<[^<]+?>', '', user_bio).strip()[:160]}">
    <meta property="og:title" content="@{username}@{instance_name}">
    <meta property="og:description" content="{re.sub(r'<[^<]+?>', '', user_bio).strip()[:160]}">
    <meta property="og:type" content="profile">
    <meta property="og:image" content="{og_image_url if og_image_url else background_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <link rel="icon" type="image/png" href="{avatar}">
    <style>
{CSS_STYLES}
    </style>
</head>
<body>
{html_body}
    <script>
        const postsData = {posts_json};

{JAVASCRIPT_CODE}
    </script>
</body>
</html>"""
    return html_output