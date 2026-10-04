import datetime
from collections import defaultdict

def parse_iso_datetime(dt_str, tz_offset_hours=8):
    """解析 ISO 8601 时间戳并转换至指定时区（默认 UTC+8）"""
    if not dt_str:
        return None
    try:
        # 支持以 Z 结尾或带偏移量的格式
        dt_str = dt_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(dt_str)
        # 转为目标时区
        target_tz = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
        return dt.astimezone(target_tz)
    except Exception:
        return None

class RepoDataAnalyzer:
    def __init__(self, user_info, repos, repo_commits_map, tz_offset_hours=8):
        self.user_info = user_info or {}
        self.repos = repos or []
        self.repo_commits_map = repo_commits_map or {}
        self.tz_offset_hours = tz_offset_hours
        
        self.user_login = (self.user_info.get("login") or "").lower()
        self.user_name = (self.user_info.get("name") or "").lower()
        self.user_email = (self.user_info.get("email") or "quincy.zou@gmail.com").lower()

    def is_user_commit(self, commit):
        """判断提交是否为当前用户产出"""
        c_login = (commit.get("login") or "").lower()
        c_name = (commit.get("author_name") or "").lower()
        c_email = (commit.get("author_email") or "").lower()
        
        if c_login and c_login == self.user_login:
            return True
        if self.user_name and c_name and self.user_name in c_name:
            return True
        if self.user_email and c_email and self.user_email in c_email:
            return True
        # famotime 或 quincy zou 特征匹配
        if "famotime" in c_name or "famotime" in c_email or "quincy" in c_name:
            return True
        return False

    def analyze(self):
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        # 统计容器
        hourly_user = [0] * 24
        hourly_total = [0] * 24
        weekday_user = [0] * 7
        weekday_total = [0] * 7
        punchcard_map = defaultdict(lambda: {"user": 0, "total": 0})  # (weekday_idx, hour): {user, total}
        
        monthly_user = defaultdict(int)
        monthly_total = defaultdict(int)
        yearly_user = defaultdict(int)
        yearly_total = defaultdict(int)
        
        total_commits = 0
        user_commits = 0
        
        repo_details = []
        all_commit_dates = []
        
        # 遍历各个仓库
        for repo in self.repos:
            repo_name = repo["name"]
            commits = self.repo_commits_map.get(repo_name, [])
            
            repo_total_commits = len(commits)
            repo_user_commits = 0
            repo_dates = []
            
            for c in commits:
                total_commits += 1
                is_mine = self.is_user_commit(c)
                if is_mine:
                    user_commits += 1
                    repo_user_commits += 1
                
                dt = parse_iso_datetime(c.get("date"), self.tz_offset_hours)
                if not dt:
                    dt = parse_iso_datetime(c.get("committer_date"), self.tz_offset_hours)
                
                if dt:
                    repo_dates.append(dt)
                    all_commit_dates.append(dt)
                    
                    hour = dt.hour
                    weekday = dt.weekday()  # 0=Monday, 6=Sunday
                    month_key = dt.strftime("%Y-%m")
                    year_key = dt.strftime("%Y")
                    
                    hourly_total[hour] += 1
                    weekday_total[weekday] += 1
                    punchcard_map[(weekday, hour)]["total"] += 1
                    monthly_total[month_key] += 1
                    yearly_total[year_key] += 1
                    
                    if is_mine:
                        hourly_user[hour] += 1
                        weekday_user[weekday] += 1
                        punchcard_map[(weekday, hour)]["user"] += 1
                        monthly_user[month_key] += 1
                        yearly_user[year_key] += 1

            repo_dates.sort()
            first_commit_str = repo_dates[0].strftime("%Y-%m-%d") if repo_dates else "-"
            latest_commit_str = repo_dates[-1].strftime("%Y-%m-%d") if repo_dates else "-"
            
            c_dt = parse_iso_datetime(repo.get("created_at"), self.tz_offset_hours)
            u_dt = parse_iso_datetime(repo.get("updated_at"), self.tz_offset_hours)
            p_dt = parse_iso_datetime(repo.get("pushed_at"), self.tz_offset_hours)
            
            repo_details.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description") or "暂无描述",
                "html_url": repo.get("html_url"),
                "is_private": repo.get("private", False),
                "created_at": c_dt.strftime("%Y-%m-%d %H:%M") if c_dt else "-",
                "created_date": c_dt.strftime("%Y-%m-%d") if c_dt else "",
                "updated_at": u_dt.strftime("%Y-%m-%d %H:%M") if u_dt else "-",
                "pushed_at": p_dt.strftime("%Y-%m-%d %H:%M") if p_dt else "-",
                "pushed_date": p_dt.strftime("%Y-%m-%d") if p_dt else "",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "size_kb": repo.get("size", 0),
                "language": repo.get("language") or "其他",
                "default_branch": repo.get("default_branch", "main"),
                "topics": repo.get("topics", []),
                "total_commits": repo_total_commits,
                "user_commits": repo_user_commits,
                "first_commit": first_commit_str,
                "latest_commit": latest_commit_str
            })

        # 整理月度趋势（按时间正序排列）
        all_months = sorted(list(set(list(monthly_total.keys()) + list(monthly_user.keys()))))
        monthly_trend = {
            "categories": all_months,
            "user": [monthly_user[m] for m in all_months],
            "total": [monthly_total[m] for m in all_months]
        }
        
        # 整理打卡矩阵 Punchcard: [day_idx, hour, user_count, total_count]
        punchcard_data = []
        for w in range(7):
            for h in range(24):
                item = punchcard_map[(w, h)]
                punchcard_data.append([w, h, item["user"], item["total"]])

        # 语言统计
        lang_counts = defaultdict(int)
        lang_sizes = defaultdict(int)
        for r in repo_details:
            lang = r["language"]
            lang_counts[lang] += 1
            lang_sizes[lang] += r["size_kb"]
        
        sorted_languages = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        language_stats = [
            {"name": k, "count": v, "size_kb": lang_sizes[k]}
            for k, v in sorted_languages
        ]

        # 核心指标卡片
        total_repos_count = len(repo_details)
        total_stars = sum(r["stars"] for r in repo_details)
        total_forks = sum(r["forks"] for r in repo_details)
        user_commit_ratio = round((user_commits / total_commits * 100), 1) if total_commits > 0 else 0
        
        # 最值计算
        sorted_by_stars = sorted(repo_details, key=lambda x: x["stars"], reverse=True)
        sorted_by_commits = sorted(repo_details, key=lambda x: x["total_commits"], reverse=True)
        sorted_by_forks = sorted(repo_details, key=lambda x: x["forks"], reverse=True)
        
        top_stars = sorted_by_stars[:10]
        top_commits = sorted_by_commits[:10]
        top_forks = sorted_by_forks[:10]

        peak_hour_user = max(range(24), key=lambda h: hourly_user[h]) if any(hourly_user) else 0
        peak_hour_total = max(range(24), key=lambda h: hourly_total[h]) if any(hourly_total) else 0
        peak_weekday_user = weekday_names[max(range(7), key=lambda w: weekday_user[w])] if any(weekday_user) else "-"
        peak_weekday_total = weekday_names[max(range(7), key=lambda w: weekday_total[w])] if any(weekday_total) else "-"

        all_commit_dates.sort()
        earliest_commit_str = all_commit_dates[0].strftime("%Y-%m-%d") if all_commit_dates else "-"
        latest_commit_str = all_commit_dates[-1].strftime("%Y-%m-%d") if all_commit_dates else "-"

        summary = {
            "total_repos": total_repos_count,
            "total_commits": total_commits,
            "user_commits": user_commits,
            "user_commit_ratio": user_commit_ratio,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "language_count": len(language_stats),
            "peak_hour_user": f"{peak_hour_user}:00 - {peak_hour_user+1}:00",
            "peak_weekday_user": peak_weekday_user,
            "earliest_commit": earliest_commit_str,
            "latest_commit": latest_commit_str,
            "user_login": self.user_login,
            "user_name": self.user_info.get("name") or self.user_login,
            "avatar_url": self.user_info.get("avatar_url") or "",
            "bio": self.user_info.get("bio") or "",
            "public_repos": self.user_info.get("public_repos", 0),
            "followers": self.user_info.get("followers", 0),
            "created_at": parse_iso_datetime(self.user_info.get("created_at"), self.tz_offset_hours).strftime("%Y-%m-%d") if self.user_info.get("created_at") else "-"
        }

        return {
            "summary": summary,
            "repo_details": repo_details,
            "hourly": {
                "hours": [f"{h}:00" for h in range(24)],
                "user": hourly_user,
                "total": hourly_total
            },
            "weekday": {
                "names": weekday_names,
                "user": weekday_user,
                "total": weekday_total
            },
            "punchcard": punchcard_data,
            "monthly_trend": monthly_trend,
            "language_stats": language_stats,
            "top_stars": top_stars,
            "top_commits": top_commits,
            "top_forks": top_forks
        }
