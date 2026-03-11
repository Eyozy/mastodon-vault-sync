const POSTS_PER_PAGE = 40;
let currentPage = 1;
let currentPosts = [];
let filteredPosts = [];

document.addEventListener('DOMContentLoaded', function () {
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

    prevBtn.addEventListener('click', function () {
        if (currentPage > 1) {
            currentPage--;
            renderCurrentPage();
            window.scrollTo(0, 0);
        }
    });

    nextBtn.addEventListener('click', function () {
        const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);
        if (currentPage < totalPages) {
            currentPage++;
            renderCurrentPage();
            window.scrollTo(0, 0);
        }
    });

    document.addEventListener('keydown', function (e) {
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

    searchInput.addEventListener('input', function () {
        const query = this.value.trim();
        clearBtn.classList.toggle('show', query.length > 0);

        const filteredPosts = query
            ? filterPosts(postsData, query)
            : postsData;

        renderPosts(filteredPosts);
    });

    clearBtn.addEventListener('click', function () {
        searchInput.value = '';
        this.classList.remove('show');
        renderPosts(postsData);
        searchInput.focus();
    });

    searchInput.addEventListener('keydown', function (e) {
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

    themeToggle.addEventListener('click', function () {
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

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
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
        img.addEventListener('click', function () {
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
        closeBtn.onclick = function () {
            modal.style.display = 'none';
        };

        // 点击模态框背景关闭
        modal.onclick = function (e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };

        // 按 ESC 键关闭
        document.addEventListener('keydown', function (e) {
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

window.addEventListener('scroll', function () {
    if (window.pageYOffset > 300) {
        backToTopBtn.classList.add('show');
    } else {
        backToTopBtn.classList.remove('show');
    }
});

backToTopBtn.addEventListener('click', function () {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Home' && !e.target.matches('input, textarea, select')) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
});
