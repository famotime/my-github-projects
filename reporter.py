import json
import datetime
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub 项目与提交分布可视化报告 - {{USER_NAME}}</title>
    <!-- ECharts 5 CDN -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <script>
        if (typeof echarts === 'undefined') {
            document.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"><\\/script>');
        }
    </script>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-card: #21262d;
            --bg-hover: #30363d;
            --border-color: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-color: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #bc8cff;
            --accent-orange: #f0883e;
            --accent-yellow: #d29922;
            --tag-bg: #21262d;
            --shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }

        [data-theme="light"] {
            --bg-primary: #f6f8fa;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --bg-hover: #f3f4f6;
            --border-color: #d0d7de;
            --text-primary: #1f2328;
            --text-secondary: #656d76;
            --text-muted: #8c959f;
            --accent-color: #0969da;
            --accent-green: #1a7f37;
            --accent-purple: #8250df;
            --accent-orange: #bc4c00;
            --accent-yellow: #9a6700;
            --tag-bg: #eff1f3;
            --shadow: 0 4px 16px rgba(140, 149, 159, 0.15);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            transition: background-color 0.25s ease, border-color 0.25s ease, color 0.2s ease;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 24px 32px 64px;
            max-width: 1440px;
            margin: 0 auto;
        }

        /* 顶部导航与用户信息 */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 24px 32px;
            margin-bottom: 28px;
            box-shadow: var(--shadow);
            flex-wrap: wrap;
            gap: 20px;
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .user-avatar {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            border: 3px solid var(--accent-color);
            object-fit: cover;
        }

        .user-info h1 {
            font-size: 24px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-info h1 span.username {
            font-size: 16px;
            font-weight: 400;
            color: var(--text-secondary);
        }

        .user-bio {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
            max-width: 650px;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .theme-btn, .mode-toggle-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
        }

        .theme-btn:hover, .mode-toggle-btn:hover {
            background: var(--bg-hover);
        }

        /* 提交作者筛选开关 */
        .filter-switch-group {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 3px;
        }

        .filter-switch-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        }

        .filter-switch-btn.active {
            background: var(--accent-color);
            color: #ffffff;
        }

        /* KPI 指标卡片网格 */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px;
            margin-bottom: 28px;
        }

        .metric-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent-color);
        }

        .metric-card.green::before { background: var(--accent-green); }
        .metric-card.purple::before { background: var(--accent-purple); }
        .metric-card.orange::before { background: var(--accent-orange); }
        .metric-card.yellow::before { background: var(--accent-yellow); }

        .metric-label {
            font-size: 13px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .metric-value {
            font-size: 26px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.1;
        }

        .metric-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }

        /* 图表容器网格 */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 28px;
        }

        @media (max-width: 1024px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 22px;
            box-shadow: var(--shadow);
        }

        .chart-card.full-width {
            grid-column: 1 / -1;
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .chart-title {
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-subtitle {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .chart-container {
            width: 100%;
            height: 340px;
        }

        .chart-container.large {
            height: 420px;
        }

        /* 仓库表格模块 */
        .table-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 24px;
            box-shadow: var(--shadow);
        }

        .table-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 20px;
        }

        .search-box {
            position: relative;
            flex: 1;
            max-width: 360px;
        }

        .search-input {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px 14px 8px 36px;
            color: var(--text-primary);
            font-size: 14px;
            outline: none;
        }

        .search-input:focus {
            border-color: var(--accent-color);
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            fill: var(--text-muted);
            width: 16px;
            height: 16px;
        }

        .filter-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .filter-pill {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 500;
        }

        .filter-pill.active {
            background: var(--accent-color);
            color: #ffffff;
            border-color: var(--accent-color);
        }

        .filter-actions {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .form-select {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
            cursor: pointer;
            font-weight: 500;
        }

        .form-select:hover {
            background-color: var(--bg-hover);
            border-color: var(--accent-color);
        }

        .form-select:focus {
            border-color: var(--accent-color);
        }

        .page-size-selector {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .table-wrapper {
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }

        th {
            background: var(--bg-card);
            color: var(--text-secondary);
            padding: 12px 14px;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
            border-bottom: 1px solid var(--border-color);
        }

        th:hover {
            color: var(--accent-color);
        }

        th.sorted-asc::after { content: " ↑"; color: var(--accent-color); }
        th.sorted-desc::after { content: " ↓"; color: var(--accent-color); }

        td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: var(--bg-hover);
        }

        .repo-link {
            font-weight: 600;
            color: var(--accent-color);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .repo-link:hover {
            text-decoration: underline;
        }

        .badge {
            display: inline-block;
            font-size: 11px;
            padding: 2px 7px;
            border-radius: 12px;
            font-weight: 500;
        }

        .badge-public {
            background: rgba(63, 185, 80, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(63, 185, 80, 0.3);
        }

        .badge-private {
            background: rgba(240, 136, 62, 0.15);
            color: var(--accent-orange);
            border: 1px solid rgba(240, 136, 62, 0.3);
        }

        .lang-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .lang-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
        }

        .pagination {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 18px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .page-buttons {
            display: flex;
            gap: 8px;
        }

        .page-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }

        .page-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        footer {
            margin-top: 48px;
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
        }
    </style>
</head>
<body data-theme="dark">

    <header>
        <div class="user-profile">
            <img class="user-avatar" src="{{AVATAR_URL}}" alt="{{USER_NAME}}">
            <div class="user-info">
                <h1>{{USER_NAME}} <span class="username">@{{USER_LOGIN}}</span></h1>
                <div class="user-bio">{{BIO}}</div>
            </div>
        </div>
        <div class="header-actions">
            <!-- 提交范围切换 -->
            <div class="filter-switch-group">
                <button class="filter-switch-btn active" id="btn-scope-user" onclick="switchScope('user')">本人提交</button>
                <button class="filter-switch-btn" id="btn-scope-total" onclick="switchScope('total')">全员提交</button>
            </div>
            <!-- 主题切换 -->
            <button class="theme-btn" onclick="toggleTheme()">
                <span id="theme-icon">☀️ 浅色</span>
            </button>
        </div>
    </header>

    <!-- KPI 关键指标总览 -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">原创仓库数</div>
            <div class="metric-value">{{TOTAL_REPOS}}</div>
            <div class="metric-sub">公开 {{PUBLIC_REPOS}} / 私有 {{PRIVATE_REPOS}}</div>
        </div>
        <div class="metric-card green">
            <div class="metric-label">总提交量 (本人贡献)</div>
            <div class="metric-value">{{USER_COMMITS}} <span style="font-size:16px;font-weight:400;color:var(--text-secondary)">/ {{TOTAL_COMMITS}}</span></div>
            <div class="metric-sub">个人代码贡献率 {{USER_COMMIT_RATIO}}%</div>
        </div>
        <div class="metric-card yellow">
            <div class="metric-label">累计获 Star</div>
            <div class="metric-value">★ {{TOTAL_STARS}}</div>
            <div class="metric-sub">最高获 Star: {{TOP_STAR_REPO}}</div>
        </div>
        <div class="metric-card purple">
            <div class="metric-label">累计被 Fork</div>
            <div class="metric-value">⑂ {{TOTAL_FORKS}}</div>
            <div class="metric-sub">最高被 Fork: {{TOP_FORK_REPO}}</div>
        </div>
        <div class="metric-card orange">
            <div class="metric-label">涉及主要语言</div>
            <div class="metric-value">{{LANGUAGE_COUNT}} 种</div>
            <div class="metric-sub">主要开发语言: {{TOP_LANGUAGE}}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">黄金时段 & 最活跃日</div>
            <div class="metric-value" style="font-size:20px">{{PEAK_HOUR_USER}}</div>
            <div class="metric-sub">最活跃日: {{PEAK_WEEKDAY_USER}}</div>
        </div>
        <div class="metric-card green">
            <div class="metric-label">提交统计跨度</div>
            <div class="metric-value" style="font-size:18px">{{EARLIEST_COMMIT}}</div>
            <div class="metric-sub">至 {{LATEST_COMMIT}}</div>
        </div>
    </div>

    <!-- 图表分析网格 -->
    <div class="charts-grid">
        <!-- 24小时分布 -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">⏱️ 24 小时活跃时段分布</div>
                    <div class="chart-subtitle">统计代码提交在一天中的作息时间分布</div>
                </div>
            </div>
            <div id="chart-hourly" class="chart-container"></div>
        </div>

        <!-- 星期活跃分布 -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">📅 星期活跃度分布</div>
                    <div class="chart-subtitle">周一至周日提交频次统计 (工作日 vs 周末)</div>
                </div>
            </div>
            <div id="chart-weekday" class="chart-container"></div>
        </div>

        <!-- 打卡热力气泡图 (Punchcard) -->
        <div class="chart-card full-width">
            <div class="chart-header">
                <div>
                    <div class="chart-title">🎯 星期 × 24小时 打卡热力气泡图 (GitHub Punchcard)</div>
                    <div class="chart-subtitle">纵轴为星期，横轴为时段，气泡大小与颜色深浅代表提交密集度</div>
                </div>
            </div>
            <div id="chart-punchcard" class="chart-container"></div>
        </div>

        <!-- 月度活跃趋势 -->
        <div class="chart-card full-width">
            <div class="chart-header">
                <div>
                    <div class="chart-title">📈 历年月度提交活跃趋势 (Timeline)</div>
                    <div class="chart-subtitle">支持鼠标滚轮或下方滑块缩放浏览各年份活跃起伏</div>
                </div>
            </div>
            <div id="chart-trend" class="chart-container large"></div>
        </div>

        <!-- 编程语言分布 -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">💻 编程语言分布</div>
                    <div class="chart-subtitle">按仓库主语言数量占比统计</div>
                </div>
            </div>
            <div id="chart-language" class="chart-container"></div>
        </div>

        <!-- 仓库提交量 Top 10 排行 -->
        <div class="chart-card">
            <div class="chart-header">
                <div>
                    <div class="chart-title">🏆 仓库提交量排行 Top 10</div>
                    <div class="chart-subtitle">代码提交最活跃的核心项目</div>
                </div>
            </div>
            <div id="chart-top-commits" class="chart-container"></div>
        </div>
    </div>

    <!-- 仓库明细数据表 -->
    <div class="table-section">
        <div class="chart-header">
            <div>
                <div class="chart-title">📂 仓库详细信息与指标总览 (<span id="repo-count-filtered">0</span>)</div>
                <div class="chart-subtitle">点击表头可按 Stars、Forks、提交数、大小及时间即时排序</div>
            </div>
        </div>

        <div class="table-controls">
            <div class="search-box">
                <svg class="search-icon" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M11.5 7a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0zm-.82 4.74a6 6 0 1 1 1.06-1.06l3.04 3.04a.75.75 0 1 1-1.06 1.06l-3.04-3.04z"></path></svg>
                <input type="text" id="searchInput" class="search-input" placeholder="搜索仓库名、描述、语言..." oninput="handleSearch()">
            </div>
            <div class="filter-actions">
                <div class="filter-tags">
                    <div class="filter-pill active" onclick="setFilter('all', this)">全部 ({{TOTAL_REPOS}})</div>
                    <div class="filter-pill" onclick="setFilter('public', this)">仅公开 ({{PUBLIC_REPOS}})</div>
                    <div class="filter-pill" onclick="setFilter('private', this)">仅私有 ({{PRIVATE_REPOS}})</div>
                </div>
                <select id="yearFilter" class="form-select" onchange="handleYearChange()">
                    <option value="">📅 创建年份: 全部</option>
                </select>
            </div>
        </div>

        <div class="table-wrapper">
            <table id="repoTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('name', this)">仓库名</th>
                        <th onclick="sortTable('is_private', this)">属性</th>
                        <th onclick="sortTable('language', this)">主语言</th>
                        <th onclick="sortTable('stars', this)">Stars</th>
                        <th onclick="sortTable('forks', this)">Forks</th>
                        <th onclick="sortTable('user_commits', this)">本人提交</th>
                        <th class="sorted-desc" onclick="sortTable('total_commits', this)">总提交</th>
                        <th onclick="sortTable('size_kb', this)">代码大小</th>
                        <th onclick="sortTable('created_date', this)">创建日期</th>
                        <th onclick="sortTable('pushed_date', this)">最近推送</th>
                    </tr>
                </thead>
                <tbody id="repoTableBody">
                    <!-- 动态渲染 -->
                </tbody>
            </table>
        </div>

        <div class="pagination">
            <div class="page-size-selector">
                <span>每页显示:</span>
                <select id="pageSizeSelect" class="form-select" onchange="handlePageSizeChange()">
                    <option value="15" selected>15 条</option>
                    <option value="30">30 条</option>
                    <option value="50">50 条</option>
                    <option value="100">100 条</option>
                </select>
                <span id="pageInfo" style="margin-left: 10px;">正在加载...</span>
            </div>
            <div class="page-buttons">
                <button class="page-btn" id="prevPageBtn" onclick="changePage(-1)">上一页</button>
                <button class="page-btn" id="nextPageBtn" onclick="changePage(1)">下一页</button>
            </div>
        </div>
    </div>

    <footer>
        <p>GitHub Repository & Commit Analysis Report • 报告生成于 {{REPORT_GEN_TIME}} • 时区: UTC+8</p>
    </footer>

    <script>
        // 数据注入
        const REPORT_DATA = {{DATA_JSON}};

        let currentScope = 'user'; // 'user' or 'total'
        let currentTheme = 'dark';
        let filterType = 'all'; // 'all', 'public', 'private'
        let selectedYear = '';
        let searchQuery = '';
        let sortColumn = 'total_commits';
        let sortAsc = false;
        let currentPage = 1;
        let pageSize = 15;

        // 图表实例引用
        let chartHourly, chartWeekday, chartPunchcard, chartTrend, chartLanguage, chartTopCommits;

        // 语言颜色映射
        const LANG_COLORS = {
            'Python': '#3572A5',
            'JavaScript': '#f1e05a',
            'TypeScript': '#3178c6',
            'HTML': '#e34c26',
            'CSS': '#563d7c',
            'Vue': '#41b883',
            'Go': '#00ADD8',
            'Rust': '#dea584',
            'Shell': '#89e051',
            'C++': '#f34b7d',
            'C': '#555555',
            'Jupyter Notebook': '#DA5B0B',
            '其他': '#8b949e'
        };

        function getLangColor(lang) {
            return LANG_COLORS[lang] || '#58a6ff';
        }

        function formatSize(kb) {
            if (kb < 1024) return kb + ' KB';
            return (kb / 1024).toFixed(1) + ' MB';
        }

        function toggleTheme() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-theme', currentTheme);
            document.getElementById('theme-icon').innerText = currentTheme === 'dark' ? '☀️ 浅色' : '🌙 深色';
            renderAllCharts();
        }

        function switchScope(scope) {
            currentScope = scope;
            document.getElementById('btn-scope-user').classList.toggle('active', scope === 'user');
            document.getElementById('btn-scope-total').classList.toggle('active', scope === 'total');
            renderHourlyChart();
            renderWeekdayChart();
            renderPunchcardChart();
            renderTrendChart();
        }

        function getChartThemeColors() {
            const isDark = currentTheme === 'dark';
            return {
                text: isDark ? '#c9d1d9' : '#1f2328',
                subtext: isDark ? '#8b949e' : '#656d76',
                gridLine: isDark ? '#30363d' : '#e1e4e8',
                cardBg: isDark ? '#161b22' : '#ffffff',
                tooltipBg: isDark ? '#21262d' : '#ffffff',
                tooltipBorder: isDark ? '#30363d' : '#d0d7de',
                accent: isDark ? '#58a6ff' : '#0969da',
                accentAlt: isDark ? '#3fb950' : '#1a7f37'
            };
        }

        function renderHourlyChart() {
            if (!chartHourly) chartHourly = echarts.init(document.getElementById('chart-hourly'));
            const c = getChartThemeColors();
            const hours = REPORT_DATA.hourly.hours;
            const dataUser = REPORT_DATA.hourly.user;
            const dataTotal = REPORT_DATA.hourly.total;
            const activeData = currentScope === 'user' ? dataUser : dataTotal;

            const option = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text }
                },
                grid: { top: 35, right: 25, bottom: 35, left: 45 },
                xAxis: {
                    type: 'category',
                    data: hours,
                    axisLabel: { color: c.subtext, interval: 2 },
                    axisLine: { lineStyle: { color: c.gridLine } }
                },
                yAxis: {
                    type: 'value',
                    name: '提交数',
                    nameTextStyle: { color: c.subtext },
                    splitLine: { lineStyle: { color: c.gridLine, type: 'dashed' } },
                    axisLabel: { color: c.subtext }
                },
                series: [{
                    name: currentScope === 'user' ? '本人提交' : '全员提交',
                    type: 'line',
                    smooth: true,
                    data: activeData,
                    symbolSize: 6,
                    itemStyle: { color: c.accent },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: currentScope === 'user' ? 'rgba(88, 166, 255, 0.45)' : 'rgba(63, 185, 80, 0.45)' },
                            { offset: 1, color: 'rgba(88, 166, 255, 0.02)' }
                        ])
                    }
                }]
            };
            chartHourly.setOption(option);
        }

        function renderWeekdayChart() {
            if (!chartWeekday) chartWeekday = echarts.init(document.getElementById('chart-weekday'));
            const c = getChartThemeColors();
            const names = REPORT_DATA.weekday.names;
            const activeData = currentScope === 'user' ? REPORT_DATA.weekday.user : REPORT_DATA.weekday.total;

            const option = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text }
                },
                grid: { top: 35, right: 25, bottom: 35, left: 45 },
                xAxis: {
                    type: 'category',
                    data: names,
                    axisLabel: { color: c.subtext },
                    axisLine: { lineStyle: { color: c.gridLine } }
                },
                yAxis: {
                    type: 'value',
                    name: '提交数',
                    nameTextStyle: { color: c.subtext },
                    splitLine: { lineStyle: { color: c.gridLine, type: 'dashed' } },
                    axisLabel: { color: c.subtext }
                },
                series: [{
                    name: currentScope === 'user' ? '本人提交' : '全员提交',
                    type: 'bar',
                    barWidth: '45%',
                    data: activeData,
                    itemStyle: {
                        borderRadius: [6, 6, 0, 0],
                        color: function (params) {
                            if (params.dataIndex >= 5) {
                                return currentTheme === 'dark' ? '#f0883e' : '#bc4c00';
                            }
                            return c.accent;
                        }
                    }
                }]
            };
            chartWeekday.setOption(option);
        }

        function renderPunchcardChart() {
            if (!chartPunchcard) chartPunchcard = echarts.init(document.getElementById('chart-punchcard'));
            const c = getChartThemeColors();
            const hours = REPORT_DATA.hourly.hours;
            const days = REPORT_DATA.weekday.names;
            
            const punchData = REPORT_DATA.punchcard.map(item => {
                const count = currentScope === 'user' ? item[2] : item[3];
                return [item[1], item[0], count];
            });

            const maxCount = Math.max(...punchData.map(d => d[2]), 1);

            const option = {
                tooltip: {
                    position: 'top',
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text },
                    formatter: function (params) {
                        return `${days[params.value[1]]} ${params.value[0]}:00<br/>提交次数: <b>${params.value[2]}</b>`;
                    }
                },
                grid: { top: 25, right: 40, bottom: 35, left: 60 },
                xAxis: {
                    type: 'category',
                    data: hours,
                    boundaryGap: false,
                    splitLine: { show: true, lineStyle: { color: c.gridLine, type: 'dashed' } },
                    axisLine: { show: false },
                    axisLabel: { color: c.subtext }
                },
                yAxis: {
                    type: 'category',
                    data: days,
                    axisLine: { show: false },
                    axisLabel: { color: c.subtext }
                },
                series: [{
                    name: '打卡热力',
                    type: 'scatter',
                    data: punchData,
                    symbolSize: function (val) {
                        if (val[2] === 0) return 0;
                        return Math.max(6, Math.min(26, Math.sqrt(val[2] / maxCount) * 26));
                    },
                    itemStyle: {
                        color: function (params) {
                            const ratio = params.value[2] / maxCount;
                            if (currentTheme === 'dark') {
                                return `rgba(88, 166, 255, ${0.35 + ratio * 0.65})`;
                            } else {
                                return `rgba(9, 105, 218, ${0.4 + ratio * 0.6})`;
                            }
                        }
                    }
                }]
            };
            chartPunchcard.setOption(option);
        }

        function renderTrendChart() {
            if (!chartTrend) chartTrend = echarts.init(document.getElementById('chart-trend'));
            const c = getChartThemeColors();
            const months = REPORT_DATA.monthly_trend.categories;
            const dataUser = REPORT_DATA.monthly_trend.user;
            const dataTotal = REPORT_DATA.monthly_trend.total;
            const activeData = currentScope === 'user' ? dataUser : dataTotal;

            const startPercent = months.length > 24 ? Math.floor((1 - 24 / months.length) * 100) : 0;

            const option = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text }
                },
                grid: { top: 35, right: 30, bottom: 70, left: 55 },
                xAxis: {
                    type: 'category',
                    data: months,
                    axisLabel: { color: c.subtext, rotate: 30 },
                    axisLine: { lineStyle: { color: c.gridLine } }
                },
                yAxis: {
                    type: 'value',
                    name: '提交量',
                    nameTextStyle: { color: c.subtext },
                    splitLine: { lineStyle: { color: c.gridLine, type: 'dashed' } },
                    axisLabel: { color: c.subtext }
                },
                dataZoom: [
                    { type: 'inside', start: startPercent, end: 100 },
                    { type: 'slider', start: startPercent, end: 100, bottom: 15, textStyle: { color: c.subtext } }
                ],
                series: [{
                    name: currentScope === 'user' ? '本人提交' : '全员提交',
                    type: 'line',
                    smooth: true,
                    data: activeData,
                    itemStyle: { color: c.accentAlt },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(63, 185, 80, 0.45)' },
                            { offset: 1, color: 'rgba(63, 185, 80, 0.02)' }
                        ])
                    }
                }]
            };
            chartTrend.setOption(option);
        }

        function renderLanguageChart() {
            if (!chartLanguage) chartLanguage = echarts.init(document.getElementById('chart-language'));
            const c = getChartThemeColors();
            const langData = REPORT_DATA.language_stats.map(l => ({
                name: l.name,
                value: l.count
            }));

            const option = {
                tooltip: {
                    trigger: 'item',
                    formatter: '{b}: {c} 个仓库 ({d}%)',
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text }
                },
                legend: {
                    bottom: 0,
                    textStyle: { color: c.subtext }
                },
                series: [{
                    name: '主要语言',
                    type: 'pie',
                    radius: ['42%', '70%'],
                    center: ['50%', '45%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 6,
                        borderColor: c.cardBg,
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold',
                            formatter: '{b}\\n{c} 仓库'
                        }
                    },
                    data: langData
                }]
            };
            chartLanguage.setOption(option);
        }

        function renderTopCommitsChart() {
            if (!chartTopCommits) chartTopCommits = echarts.init(document.getElementById('chart-top-commits'));
            const c = getChartThemeColors();
            const topRepos = [...REPORT_DATA.top_commits].reverse();
            const names = topRepos.map(r => r.name);
            const userCounts = topRepos.map(r => r.user_commits);
            const totalCounts = topRepos.map(r => r.total_commits);

            const option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    backgroundColor: c.tooltipBg,
                    borderColor: c.tooltipBorder,
                    textStyle: { color: c.text }
                },
                legend: {
                    top: 0,
                    textStyle: { color: c.subtext }
                },
                grid: { top: 35, right: 35, bottom: 25, left: 160 },
                xAxis: {
                    type: 'value',
                    splitLine: { lineStyle: { color: c.gridLine, type: 'dashed' } },
                    axisLabel: { color: c.subtext }
                },
                yAxis: {
                    type: 'category',
                    data: names,
                    axisLabel: {
                        color: c.text,
                        formatter: function (value) {
                            return value.length > 18 ? value.slice(0, 16) + '...' : value;
                        }
                    }
                },
                series: [
                    {
                        name: '本人提交',
                        type: 'bar',
                        stack: 'total',
                        data: userCounts,
                        itemStyle: { color: c.accent }
                    },
                    {
                        name: '其他提交',
                        type: 'bar',
                        stack: 'total',
                        data: totalCounts.map((tot, idx) => Math.max(0, tot - userCounts[idx])),
                        itemStyle: { color: c.gridLine }
                    }
                ]
            };
            chartTopCommits.setOption(option);
        }

        function renderAllCharts() {
            renderHourlyChart();
            renderWeekdayChart();
            renderPunchcardChart();
            renderTrendChart();
            renderLanguageChart();
            renderTopCommitsChart();
        }

        // 表格渲染与交互逻辑
        let filteredRepos = [...REPORT_DATA.repo_details];

        function setFilter(type, el) {
            filterType = type;
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            el.classList.add('active');
            currentPage = 1;
            applyFilters();
        }

        function handleYearChange() {
            selectedYear = document.getElementById('yearFilter').value;
            currentPage = 1;
            applyFilters();
        }

        function handlePageSizeChange() {
            pageSize = parseInt(document.getElementById('pageSizeSelect').value, 10) || 15;
            currentPage = 1;
            renderTablePage();
        }

        function initYearFilter() {
            const yearSet = new Set();
            REPORT_DATA.repo_details.forEach(r => {
                if (r.created_date && r.created_date.includes('-')) {
                    const yr = r.created_date.split('-')[0].trim();
                    if (yr) yearSet.add(yr);
                }
            });
            const sortedYears = Array.from(yearSet).sort().reverse();
            const yearSelect = document.getElementById('yearFilter');
            sortedYears.forEach(y => {
                const opt = document.createElement('option');
                opt.value = y;
                opt.innerText = `📅 ${y} 年`;
                yearSelect.appendChild(opt);
            });
        }

        function handleSearch() {
            searchQuery = document.getElementById('searchInput').value.trim().toLowerCase();
            currentPage = 1;
            applyFilters();
        }

        function applyFilters() {
            filteredRepos = REPORT_DATA.repo_details.filter(r => {
                if (filterType === 'public' && r.is_private) return false;
                if (filterType === 'private' && !r.is_private) return false;
                if (selectedYear) {
                    if (!r.created_date || !r.created_date.startsWith(selectedYear)) return false;
                }
                if (searchQuery) {
                    const matchName = r.name.toLowerCase().includes(searchQuery);
                    const matchDesc = (r.description || '').toLowerCase().includes(searchQuery);
                    const matchLang = (r.language || '').toLowerCase().includes(searchQuery);
                    if (!matchName && !matchDesc && !matchLang) return false;
                }
                return true;
            });

            // 排序
            filteredRepos.sort((a, b) => {
                let vA = a[sortColumn];
                let vB = b[sortColumn];
                if (typeof vA === 'string') {
                    return sortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
                }
                return sortAsc ? (vA - vB) : (vB - vA);
            });

            document.getElementById('repo-count-filtered').innerText = filteredRepos.length;
            renderTablePage();
        }

        function sortTable(column, thElement) {
            if (sortColumn === column) {
                sortAsc = !sortAsc;
            } else {
                sortColumn = column;
                sortAsc = false;
            }

            document.querySelectorAll('th').forEach(th => th.className = '');
            if (thElement) {
                thElement.className = sortAsc ? 'sorted-asc' : 'sorted-desc';
            }
            applyFilters();
        }

        function changePage(delta) {
            currentPage += delta;
            renderTablePage();
        }

        function renderTablePage() {
            const tbody = document.getElementById('repoTableBody');
            tbody.innerHTML = '';

            const total = filteredRepos.length;
            const totalPages = Math.ceil(total / pageSize) || 1;
            currentPage = Math.max(1, Math.min(currentPage, totalPages));

            const startIdx = (currentPage - 1) * pageSize;
            const endIdx = Math.min(startIdx + pageSize, total);
            const currentSlice = filteredRepos.slice(startIdx, endIdx);

            currentSlice.forEach(r => {
                const tr = document.createElement('tr');
                const langColor = getLangColor(r.language);
                tr.innerHTML = `
                    <td>
                        <a class="repo-link" href="${r.html_url}" target="_blank" title="${r.description}">
                            ${r.name}
                        </a>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.description}</div>
                    </td>
                    <td>
                        <span class="badge ${r.is_private ? 'badge-private' : 'badge-public'}">
                            ${r.is_private ? '私有' : '公开'}
                        </span>
                    </td>
                    <td>
                        <span class="lang-indicator">
                            <span class="lang-dot" style="background:${langColor}"></span>
                            ${r.language}
                        </span>
                    </td>
                    <td style="font-weight:600">★ ${r.stars}</td>
                    <td>⑂ ${r.forks}</td>
                    <td style="color:var(--accent-color);font-weight:600">${r.user_commits}</td>
                    <td>${r.total_commits}</td>
                    <td style="color:var(--text-secondary)">${formatSize(r.size_kb)}</td>
                    <td style="color:var(--text-secondary)">${r.created_date}</td>
                    <td style="color:var(--text-secondary)">${r.pushed_date}</td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('pageInfo').innerText = `显示第 ${total > 0 ? startIdx + 1 : 0} 至 ${endIdx} 条，共 ${total} 条 (第 ${currentPage}/${totalPages} 页)`;
            document.getElementById('prevPageBtn').disabled = currentPage <= 1;
            document.getElementById('nextPageBtn').disabled = currentPage >= totalPages;
        }

        window.addEventListener('resize', () => {
            if (chartHourly) chartHourly.resize();
            if (chartWeekday) chartWeekday.resize();
            if (chartPunchcard) chartPunchcard.resize();
            if (chartTrend) chartTrend.resize();
            if (chartLanguage) chartLanguage.resize();
            if (chartTopCommits) chartTopCommits.resize();
        });

        document.addEventListener('DOMContentLoaded', () => {
            initYearFilter();
            renderAllCharts();
            applyFilters();
        });
    </script>
</body>
</html>
"""

def generate_html_report(analyzed_data, output_path):
    summary = analyzed_data["summary"]
    repo_details = analyzed_data["repo_details"]
    
    private_repos_count = sum(1 for r in repo_details if r["is_private"])
    public_repos_count = len(repo_details) - private_repos_count
    
    top_star_repo = analyzed_data["top_stars"][0]["name"] if analyzed_data["top_stars"] else "-"
    top_fork_repo = analyzed_data["top_forks"][0]["name"] if analyzed_data["top_forks"] else "-"
    top_language = analyzed_data["language_stats"][0]["name"] if analyzed_data["language_stats"] else "-"
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    replacements = {
        "{{USER_NAME}}": str(summary.get("user_name") or summary.get("user_login")),
        "{{USER_LOGIN}}": str(summary.get("user_login")),
        "{{AVATAR_URL}}": str(summary.get("avatar_url")),
        "{{BIO}}": str(summary.get("bio") or "这个人很懒，什么都没写~"),
        "{{TOTAL_REPOS}}": str(summary.get("total_repos")),
        "{{PUBLIC_REPOS}}": str(public_repos_count),
        "{{PRIVATE_REPOS}}": str(private_repos_count),
        "{{USER_COMMITS}}": str(summary.get("user_commits")),
        "{{TOTAL_COMMITS}}": str(summary.get("total_commits")),
        "{{USER_COMMIT_RATIO}}": str(summary.get("user_commit_ratio")),
        "{{TOTAL_STARS}}": str(summary.get("total_stars")),
        "{{TOP_STAR_REPO}}": str(top_star_repo),
        "{{TOTAL_FORKS}}": str(summary.get("total_forks")),
        "{{TOP_FORK_REPO}}": str(top_fork_repo),
        "{{LANGUAGE_COUNT}}": str(summary.get("language_count")),
        "{{TOP_LANGUAGE}}": str(top_language),
        "{{PEAK_HOUR_USER}}": str(summary.get("peak_hour_user")),
        "{{PEAK_WEEKDAY_USER}}": str(summary.get("peak_weekday_user")),
        "{{EARLIEST_COMMIT}}": str(summary.get("earliest_commit")),
        "{{LATEST_COMMIT}}": str(summary.get("latest_commit")),
        "{{REPORT_GEN_TIME}}": now_str,
        "{{DATA_JSON}}": json.dumps(analyzed_data, ensure_ascii=False)
    }

    content = HTML_TEMPLATE
    for key, val in replacements.items():
        content = content.replace(key, val)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[报告生成] 成功生成 HTML 报告: {out_file.resolve()}")
    return out_file.resolve()
