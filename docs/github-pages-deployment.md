# GitHub Pages 报告网页发布与自动化部署指南

本文档提供将本项目生成的 GitHub 可视化分析报告网页（默认输出至 `docs/index.html`）发布至 GitHub Pages 的完整操作指导。发布后，您即可通过公网链接（如 `https://<用户名>.github.io/<仓库名>/`）在手机、平板或任何电脑浏览器中随时查阅您的 GitHub 研发仪表盘。

---

## 目录

- [一、准备工作与注意事项](#一准备工作与注意事项)
  - [1. 关键注意：默认入口文件命名规范](#1-关键注意默认入口文件命名规范)
  - [2. 隐私与安全提示（重要）](#2-隐私与安全提示重要)
- [二、发布方案汇总与选择建议](#二发布方案汇总与选择建议)
- [三、方案一：通过 `/docs` 目录发布（极简直观，推荐新手）](#三方案一通过-docs-目录发布极简直观推荐新手)
  - [步骤 1：直接生成报告至 docs 目录](#步骤-1直接生成报告至-docs-目录)
  - [步骤 2：提交并推送代码到 GitHub](#步骤-2提交并推送代码到-github)
  - [步骤 3：在 GitHub 仓库开启 Pages 服务](#步骤-3在-github-仓库开启-pages-服务)
  - [步骤 4：访问与验证](#步骤-4访问与验证)
- [四、方案二：通过根目录 `/ (root)` 发布（单页简易方案）](#四方案二通过根目录-root-发布单页简易方案)
  - [步骤 1：生成报告并命名为根目录 index.html](#步骤-1生成报告并命名为根目录-indexhtml)
  - [步骤 2：添加 .nojekyll 避免构建冲突](#步骤-2添加-nojekyll-避免构建冲突)
  - [步骤 3：提交推送并设置 Pages 根目录来源](#步骤-3提交推送并设置-pages-根目录来源)
- [五、方案三：通过独立 `gh-pages` 分支发布（主分支无噪音）](#五方案三通过独立-gh-pages-分支发布主分支无噪音)
  - [步骤 1：本地生成报告文件](#步骤-1本地生成报告文件)
  - [步骤 2：使用 Git subtree 快速推送](#步骤-2使用-git-subtree-快速推送)
  - [步骤 3：设置 Pages 分支来源](#步骤-3设置-pages-分支来源)
- [六、方案四：GitHub Actions 定时自动更新与发布（当前项目已启用）](#六方案四github-actions-定时自动更新与发布当前项目已启用)
  - [当前实际配置概览](#当前实际配置概览)
  - [步骤 1：配置 GitHub Personal Access Token (PAT)](#步骤-1配置-github-personal-access-token-pat)
  - [步骤 2：在仓库添加 Action Secret](#步骤-2在仓库添加-action-secret)
  - [步骤 3：确认 Pages 部署来源（无需改动）](#步骤-3确认-pages-部署来源无需改动)
  - [步骤 4：工作流文件（仓库已内置）](#步骤-4工作流文件仓库已内置)
  - [验证与运维要点](#验证与运维要点)
  - [可选替代模板：Pages Actions 官方构件部署](#可选替代模板pages-actions-官方构件部署)
- [七、常见问题与排查指南 (FAQ)](#七常见问题与排查指南-faq)

---

## 一、准备工作与注意事项

### 1. 关键注意：默认入口文件命名规范
GitHub Pages 默认以根目录或发布目录下的 `index.html` 作为网站首页。

本项目目前已**默认将输出报告路径配置为 `docs/index.html`**，因此您无需额外指定参数，直接运行 `python main.py` 即可开箱即用无缝契合 GitHub Pages。

若您需要指定其他自定义路径（例如输出到根目录 `index.html`），可使用 `--output` 参数：
```bash
python main.py --output index.html
```

### 2. 隐私与安全提示（重要）
> [!WARNING]
> **私有仓库数据泄露风险**：
> - 如果您的 GitHub 仓库属于 **公开仓库（Public Repository）**，其启用的 GitHub Pages 也是 **完全公开** 访问的。
> - 本工具默认会抓取您账号下的 **私有仓库（Private Repositories）** 的统计指标（包括仓库名称、提交时间、代码量等元数据）。
> - **若您不希望私有仓库名称与提交记录对外公开**：
>   1. 请将部署仓库设为私有（注意：GitHub 免费版私有仓库无法开启 Pages，需 GitHub Pro/Team）；或
>   2. 修改分析脚本排除私有仓库后再发布；或
>   3. 仅在本地运行查看，避免推送到公开的 GitHub Pages。

---

## 二、发布方案汇总与选择建议

GitHub Pages 原生支持从分支的两个指定位置进行托管：**根目录 `/ (root)`** 与 **`/docs` 目录**。此外，也可以选择独立的 **`gh-pages` 分支** 或 **GitHub Actions 自动化流**：

| 方案 | 适用场景 | 优点 | 缺点 / 风险 |
| :--- | :--- | :--- | :--- |
| **方案 A：`/docs` 目录发布（推荐）** | 个人手动维护、快速上线 | 结构清晰，源码与网站文件隔离，安全性更好 | 仓库中需包含 `docs/index.html` 文件 |
| **方案 B：根目录 `/ (root)` 发布** | 极简单页、无需额外文件夹 | 零子目录，直接把 `index.html` 放在项目根目录 | 源码与网页混杂，根目录所有文件均可通过 URL 访问 |
| **方案 C：`gh-pages` 独立分支** | 追求主分支纯净的项目 | 主分支仅存放源码，构建产物隔离在独立分支 | 手动分支同步稍繁琐 |
| **方案 D：GitHub Actions 自动流** | 长期稳定运行、自动保持最新 | **完全自动化**，可配置每天/每周定时更新，免手动运行 | 需要配置 Secret 与 Actions 工作流 |

> **当前项目实际采用**：方案 A（`/docs` 目录发布）+ 方案 D（每周日定时自动更新工作流）的组合，详见[方案四](#六方案四github-actions-定时自动更新与发布当前项目已启用)。

### 根目录 `/ (root)` vs `/docs` 目录的核心区别对比

| 对比维度 | 根目录 `/ (root)` 发布 | `/docs` 目录发布（推荐） |
| :--- | :--- | :--- |
| **首页文件位置** | 根目录下的 `index.html`（与 `main.py` 同级） | `docs/index.html` |
| **目录整洁度** | **较低**。前端报告、Python 源码、说明文档和缓存数据混杂在同一层级 | **较高**。根目录专注后端代码与工程配置，`docs` 专职存放报告网页与文档 |
| **静态资源暴露风险** | **较高**。整个仓库根目录下的所有文件（如 `analyzer.py`、`requirements.txt`）均会被当作静态资源托管，公网输入文件名即可直接下载 | **较低**。仅有 `docs/` 目录内的文件对外公开作为网站服务，根目录源码不会被静态站点路由直接暴露 |
| **Jekyll 解析与冲突** | **需要注意**。根目录下存在 `README.md`，且可能有 `_` 开头的目录（如 `__pycache__`），易触发 Jekyll 构建冲突，建议放置 `.nojekyll` 文件 | **天然纯净**。`docs/` 内部只有静态 HTML 和文档，不易发生 Jekyll 解析异常 |
| **GitHub Pages 设置项** | Branch 选 `master`，Folder 选 `/ (root)` | Branch 选 `master`，Folder 选 `/docs` |

---

## 三、方案一：通过 `/docs` 目录发布（极简直观，推荐新手）

这是 GitHub 官方原生支持的静态网站部署方式之一。

### 步骤 1：直接生成报告至 docs 目录
在项目根目录下直接运行（工具已默认输出至 `docs/index.html`）：

```bash
python main.py
```

### 步骤 2：提交并推送代码到 GitHub
在终端中执行 Git 命令提交改动：

```bash
git add docs/index.html
git commit -m "docs(report): 更新 GitHub Pages 可视化分析报告"
git push origin master
```

### 步骤 3：在 GitHub 仓库开启 Pages 服务
1. 在浏览器中打开您的 GitHub 仓库页面（例如 `https://github.com/famotime/my-github-projects`）。
2. 点击仓库顶部的 **Settings**（设置）选项卡。
3. 在左侧菜单栏中找到 **Pages**（位于 Code and automation 分类下）。
4. 在 **Build and deployment** 区域：
   - **Source** 选择：`Deploy from a branch`
   - **Branch** 选择：`master`（或 `main`），并将后面的文件夹下拉框从 `/ (root)` 改为 `/docs`
5. 点击 **Save**（保存）。

### 步骤 4：访问与验证
保存后，GitHub 会自动启动部署流程。约 1~2 分钟后刷新该页面，顶部会显示：
> *Your site is live at `https://<用户名>.github.io/<仓库名>/`*

点击链接即可查阅在线版报告仪表盘！

> **当前项目即采用此方案部署**，站点已上线：<https://famotime.github.io/my-github-projects/>；报告数据由[方案四](#六方案四github-actions-定时自动更新与发布当前项目已启用)的定时工作流每周日自动刷新，无需手动运行。

---

## 四、方案二：通过根目录 `/ (root)` 发布（单页简易方案）

如果不希望创建 `docs/` 文件夹，也可以直接将报告网页发布在仓库根目录。

### 步骤 1：生成报告并命名为根目录 `index.html`
在项目根目录运行命令，直接生成到根目录的 `index.html`：

```bash
python main.py --output index.html
```

### 步骤 2：添加 `.nojekyll` 避免构建冲突（强烈推荐）
GitHub Pages 默认使用 Jekyll 引擎解析站点。由于根目录下存在 Python 源码、`README.md` 以及可能由 Python 产生的 `__pycache__`（下划线开头目录会被 Jekyll 默认忽略或引发解析异常），建议在项目根目录下创建一个空的 `.nojekyll` 文件，通知 GitHub 完全跳过 Jekyll 引擎：

```bash
# Windows PowerShell 下创建空的 .nojekyll 文件
New-Item -ItemType File -Name ".nojekyll" -Force
```

### 步骤 3：提交推送并设置 Pages 根目录来源
1. 提交并推送到 GitHub：
   ```bash
   git add index.html .nojekyll
   git commit -m "docs(pages): 发布根目录 index.html 报告与 .nojekyll"
   git push origin master
   ```
2. 进入 GitHub 仓库 **Settings** -> **Pages**。
3. 在 **Build and deployment** 区域：
   - **Source**：选择 `Deploy from a branch`
   - **Branch**：选择 `master`，文件夹保持为默认的 **`/ (root)`**
4. 点击 **Save** 保存。

---

## 五、方案三：通过独立 `gh-pages` 分支发布（主分支无噪音）

若您不希望主分支中存在体积较大的 HTML 网页文件，可将报告发布至专门的 `gh-pages` 分支。

### 步骤 1：本地生成报告文件
```bash
python main.py --output docs/index.html
```

### 步骤 2：使用 Git subtree 快速推送
无需手动切换分支，直接使用 `git subtree` 将 `docs` 目录推送至远程 `gh-pages` 分支：

```bash
git add docs/index.html
git commit -m "chore(pages): 发布报告至 gh-pages 分支"
git subtree push --prefix docs origin gh-pages
```

### 步骤 3：设置 Pages 分支来源
1. 进入 GitHub 仓库 **Settings** -> **Pages**。
2. 将 **Branch** 选择为 `gh-pages` 分支，目录选择 `/ (root)`。
3. 点击 **Save**。

---

## 六、方案四：GitHub Actions 定时自动更新与发布（当前项目已启用）

利用 GitHub Actions，可以在云端容器中定期执行 `main.py`，自动抓取最新数据、重新生成报告并提交回仓库；配合 Pages 的分支部署模式，推送后网页即自动重建发布，彻底解放双手！

### 当前实际配置概览

| 配置项 | 当前实际值 |
| :--- | :--- |
| 工作流文件 | `.github/workflows/weekly-update.yml` |
| 定时触发 | **每周日北京时间 09:00**（`cron: '0 1 * * 0'`，GitHub 定时任务使用 UTC 时间），另支持在 Actions 页面手动触发 |
| 执行动作 | `python main.py --refresh --workers 8 --tz 8` 全量刷新 `data/*.json` 缓存并重新生成 `docs/index.html` |
| 数据回写 | 以 `github-actions[bot]` 身份将数据缓存与报告自动提交回 `master`（无变化时跳过提交） |
| Pages 部署 | 保持 **`Deploy from a branch`（`master` + `/docs`）**，push 后自动重建，**无需**切换为 GitHub Actions 模式 |
| 在线站点 | <https://famotime.github.io/my-github-projects/> |

### 步骤 1：配置 GitHub Personal Access Token (PAT)
由于需要读取用户的所有仓库与提交记录（包括私有仓库），需要生成一个 PAT：
1. 访问 GitHub [Personal Access Tokens (Tokens (classic))](https://github.com/settings/tokens)。
2. 点击 **Generate new token (classic)**。
3. 勾选权限：
   - `repo`（完整仓库权限，用以统计私有和公开仓库）
   - `read:user`（读取用户信息）
4. 复制生成的 Token（形如 `ghp_xxxx`）。

### 步骤 2：在仓库添加 Action Secret
1. 打开项目仓库，进入 **Settings** -> **Secrets and variables** -> **Actions**。
2. 点击 **New repository secret**。
3. **Name** 输入：`MY_GITHUB_TOKEN`
4. **Secret** 粘贴您刚刚复制的 Token。
5. 点击 **Add secret**。

> [!IMPORTANT]
> 此步骤**不可省略**：工作流需要读取账号下全部仓库（含私有仓库）的提交数据，而 Actions 内置的 `GITHUB_TOKEN` 无权访问 `/user`、`/user/repos` 等用户级接口，必须使用自建 PAT。

### 步骤 3：确认 Pages 部署来源（无需改动）
当前 Pages 来源为 **`Deploy from a branch`（`master` + `/docs`）**，工作流将报告提交回 `master` 后 GitHub 会自动重建页面，此步骤**无需任何改动**。

若您更希望让构建产物与主分支完全隔离（报告不提交进 `master`），可改用 GitHub Actions 官方构件部署模式：将 **Settings -> Pages -> Source** 切换为 **GitHub Actions**，并改用文末的[可选替代模板](#可选替代模板pages-actions-官方构件部署)。

### 步骤 4：工作流文件（仓库已内置）
仓库已包含 `.github/workflows/weekly-update.yml`（定时任务仅对**默认分支**上的工作流生效，当前位于 `master`，推送后即自动生效），内容如下：

```yaml
name: Weekly Data Update

on:
  schedule:
    # 每周日 UTC 01:00 = 北京时间周日 09:00 自动触发
    # (注意: GitHub 定时任务使用 UTC 时间，且高峰期可能有 10-30 分钟延迟)
    - cron: '0 1 * * 0'
  workflow_dispatch: # 支持在 Actions 页面手动一键触发

permissions:
  contents: write

concurrency:
  group: weekly-data-update
  cancel-in-progress: false

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: 检出仓库代码
        uses: actions/checkout@v4

      - name: 设置 Python 运行环境
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 安装依赖包
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: 运行分析脚本抓取最新数据并生成报告
        env:
          GITHUB_TOKEN: ${{ secrets.MY_GITHUB_TOKEN }}
        run: python main.py --refresh --workers 8 --tz 8

      - name: 提交数据缓存与报告到仓库
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A
          if git diff --cached --quiet; then
            echo "[跳过] 数据无变化，无需提交"
          else
            git commit -m "chore: 每周自动刷新数据缓存与可视化报告 [skip ci]"
            git push
          fi
```

### 验证与运维要点
- **手动触发**：仓库 **Actions -> Weekly Data Update -> Run workflow**，可用于首次验证或临时补数。
- **空提交保护**：数据无变化时工作流输出"[跳过] 数据无变化"，不会产生空 commit。
- **调度延迟**：GitHub 定时任务在高峰期常有 10~30 分钟触发延迟，属正常现象。
- **自动停用**：仓库长期（约 60 天）无任何活动时，GitHub 可能自动停用定时工作流，可在 **Actions** 页面重新启用（本项目每周边自动提交，通常不会触发此限制）。

### 可选替代模板：Pages Actions 官方构件部署

若采用 Pages 的 **GitHub Actions** 构件部署模式（报告不回写主分支，构建产物与源码完全隔离），可创建 `.github/workflows/deploy-report.yml`，内容如下：

```yaml
name: Deploy GitHub Analytics Report to Pages

on:
  push:
    branches:
      - master
  schedule:
    # 每周一上午 08:00 (UTC 00:00) 自动触发全量更新
    - cron: '0 0 * * 1'
  workflow_dispatch: # 支持在 GitHub 网页界面手动一键触发

# 赋予部署 GitHub Pages 所需的最小安全权限
permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: 'pages'
  cancel-in-progress: true

jobs:
  build-and-deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest

    steps:
      - name: 检出仓库代码
        uses: actions/checkout@v4

      - name: 设置 Python 运行环境
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 安装依赖包
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: 运行分析脚本生成报告
        env:
          GITHUB_TOKEN: ${{ secrets.MY_GITHUB_TOKEN }}
        run: |
          mkdir -p public
          # 必须携带 --refresh：云端 checkout 会包含仓库中已提交的数据缓存，
          # 不刷新会导致脚本复用旧缓存、数据无法更新
          python main.py --refresh --output public/index.html --workers 8 --tz 8

      - name: 配置 GitHub Pages 元数据
        uses: actions/configure-pages@v4

      - name: 上传构建产物至 Pages
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'public'

      - name: 执行 GitHub Pages 部署
        id: deployment
        uses: actions/deploy-pages@v4
```

推送此文件至 GitHub 后：
- 每次推送代码或点击 **Actions** 页面的 **Run workflow** 按钮，GitHub 会自动拉取数据生成仪表盘并发布。
- 每周一北京时间 08:00（UTC 00:00）定时自动更新，始终展示最新的代码活跃度与贡献统计。

---

## 七、常见问题与排查指南 (FAQ)

### Q1: 打开 GitHub Pages 链接提示 404 Not Found？
1. **检查文件名**：确保发布目录下的文件名为 `index.html`（而非 `github_report.html`）。若未命名为 `index.html`，需要通过完整链接访问，例如 `https://<用户名>.github.io/<仓库名>/github_report.html`。
2. **等待部署生效**：Pages 首次开启或更新通常需要 1~3 分钟，可在仓库 **Actions** 页面查看部署任务是否全部显示为绿色对钩。
3. **检查部署路径配置**：若使用方案一，确认 Branch 选对了 `master` 且文件夹选为 `/docs`。

### Q2: 图表不显示或页面布局乱码？
- 报告依赖公共 CDN（如 `cdn.jsdelivr.net` 加载 Apache ECharts）。请确认访问环境的网络是否能正常加载外链 JS 库。
- 按 `F12` 打开浏览器开发者工具，在 **Console (控制台)** 中查看是否有网络加载失败或资源被拦截报错。

### Q3: 部署更新后，访问网页内容依然是旧的？
- 浏览器通常会对静态 HTML 资源进行本地强缓存。
- 请尝试使用 `Ctrl + F5`（Windows）或 `Cmd + Shift + R`（Mac）强制刷新，或在无痕浏览窗口中查看。

### Q4: 如何在不同域名或自定义域名 (Custom Domain) 下访问？
- 在仓库 **Settings** -> **Pages** 的 **Custom domain** 输入框中绑定您的专属域名（例如 `report.yourdomain.com`），并按照提示在域名 DNS 服务商处添加 CNAME 解析记录即可。

### Q5: 定时自动更新工作流没有运行或没有产生新提交？
- 定时任务仅对**默认分支**（`master`）上的工作流文件生效，工作流文件推送后才会被调度识别。
- GitHub 定时任务在高峰期常有 10~30 分钟触发延迟，属正常现象。
- 运行日志显示"[跳过] 数据无变化"说明本周仓库无新提交，属预期行为。
- 仓库长期（约 60 天）无任何活动时 GitHub 可能自动停用定时工作流，可在 **Actions** 页面重新启用。
- 可随时通过 **Actions -> Weekly Data Update -> Run workflow** 手动触发。
