import argparse
import sys
import time
from pathlib import Path
from fetcher import GitHubFetcher
from analyzer import RepoDataAnalyzer
from reporter import generate_html_report

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(
        description="GitHub 个人项目详细数据分析与可视化报告生成工具"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub Personal Access Token (若不提供将自动使用 gh auth token 或环境变量)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/index.html",
        help="输出 HTML 报告文件路径 (默认: docs/index.html)"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="强制刷新所有本地缓存并从 GitHub 重新抓取"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="并发抓取线程数 (默认: 6)"
    )
    parser.add_argument(
        "--tz",
        type=int,
        default=8,
        help="时区偏移量 (小时，默认: 8 即 UTC+8 北京时间)"
    )

    args = parser.parse_args()

    start_time = time.time()
    print("=" * 60)
    print("      GitHub 项目详细信息与提交分布可视化分析工具")
    print("=" * 60)

    try:
        fetcher = GitHubFetcher(token=args.token)
        print("[认证] 正在获取 GitHub 认证用户信息...")
        user_info = fetcher.get_authenticated_user()
        username = user_info.get("login")
        print(f"[用户] 目标用户: {username} ({user_info.get('name') or '无昵称'})")

        # 获取所有原创仓库
        repos = fetcher.get_repositories(username=username, force_refresh=args.refresh)
        print(f"[仓库] 已定位 {len(repos)} 个原创仓库 (排除 Fork)")

        # 获取每个仓库的提交数据
        repo_commits_map = fetcher.fetch_all_repo_commits(
            repos=repos,
            force_refresh=args.refresh,
            max_workers=args.workers
        )

        # 数据分析与统计
        print("[分析] 正在执行多维数据统计与指标计算...")
        analyzer = RepoDataAnalyzer(
            user_info=user_info,
            repos=repos,
            repo_commits_map=repo_commits_map,
            tz_offset_hours=args.tz
        )
        analyzed_data = analyzer.analyze()

        summary = analyzed_data["summary"]
        print("-" * 60)
        print(f"  • 仓库总数: {summary['total_repos']} 个 (公开: {summary['public_repos']} / 私有: {summary['total_repos'] - summary['public_repos']})")
        print(f"  • 累计提交: {summary['total_commits']} 次 (本人贡献: {summary['user_commits']} 次, 占比: {summary['user_commit_ratio']}%)")
        print(f"  • 累计 Star: ★ {summary['total_stars']} | 累计 Fork: ⑂ {summary['total_forks']}")
        print(f"  • 涉及语言: {summary['language_count']} 种")
        print(f"  • 黄金时段: {summary['peak_hour_user']} | 最活跃: {summary['peak_weekday_user']}")
        print(f"  • 提交跨度: {summary['earliest_commit']} 至 {summary['latest_commit']}")
        print("-" * 60)

        # 生成 HTML 可视化报告
        output_file = generate_html_report(analyzed_data, args.output)

        elapsed = time.time() - start_time
        print(f"\n[成功] 报告已生成完成！耗时: {elapsed:.2f} 秒")
        print(f"[打开] 报告文件位于: {output_file}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 执行过程中发生异常: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
