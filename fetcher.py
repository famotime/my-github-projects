import os
import sys
import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CACHE_DIR = Path(__file__).parent / "data"

def get_github_token(explicit_token=None):
    if explicit_token:
        return explicit_token
    
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        return env_token
    
    # Try getting token from gh CLI
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass
    
    return None

class GitHubFetcher:
    def __init__(self, token=None, cache_dir=CACHE_DIR):
        self.token = get_github_token(token)
        if not self.token:
            raise ValueError("未检测到有效的 GitHub Token。请通过 `gh auth login` 登录，或在命令行提供 --token 参数。")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_session(self):
        s = requests.Session()
        s.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Repo-Analyzer/1.0"
        })
        return s

    def _api_get(self, session, endpoint, params=None):
        url = f"https://api.github.com{endpoint}" if endpoint.startswith("/") else endpoint
        for attempt in range(3):
            try:
                resp = session.get(url, params=params, timeout=25)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code in (403, 429):
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                    sleep_sec = max(5, reset_time - int(time.time())) if reset_time else 10
                    print(f"[警告] GitHub API 触发限速 (HTTP {resp.status_code})，等待 {sleep_sec} 秒...")
                    time.sleep(min(sleep_sec, 60))
                elif resp.status_code == 404:
                    return None
                elif resp.status_code == 409:
                    # 409 Git Repository is empty
                    return None
                else:
                    time.sleep(2)
            except requests.RequestException:
                time.sleep(2)
        return None

    def get_authenticated_user(self):
        cache_file = self.cache_dir / "user.json"
        session = self._create_session()
        resp = self._api_get(session, "/user")
        if resp and resp.status_code == 200:
            user_data = resp.json()
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            return user_data
        
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        raise RuntimeError("无法获取当前用户信息，且无本地缓存")

    def get_repositories(self, username=None, force_refresh=False):
        cache_file = self.cache_dir / f"repos_{username or 'current'}.json"
        if not force_refresh and cache_file.exists():
            print(f"[缓存] 从本地缓存加载仓库列表: {cache_file.name}")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        print("[获取] 正在从 GitHub API 抓取仓库列表...")
        session = self._create_session()
        repos = []
        page = 1
        while True:
            params = {
                "affiliation": "owner",
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "direction": "desc"
            }
            resp = self._api_get(session, "/user/repos", params=params)
            if not resp or resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        # 过滤掉 fork 仓库，只保留原创仓库
        original_repos = [r for r in repos if not r.get("fork", False)]
        print(f"[完成] 抓取完成，共获得 {len(repos)} 个仓库，其中原创仓库 {len(original_repos)} 个")
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(original_repos, f, ensure_ascii=False, indent=2)
            
        return original_repos

    def get_repo_commits(self, session, owner, repo_name, default_branch=None, pushed_at=None, force_refresh=False):
        safe_name = f"{owner}_{repo_name}".replace("/", "_")
        cache_file = self.cache_dir / f"commits_{safe_name}.json"
        
        # 智能缓存检查：如果缓存存在且 pushed_at 一致，直接复用
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    if isinstance(cache_data, dict) and "commits" in cache_data:
                        if pushed_at and cache_data.get("pushed_at") == pushed_at:
                            return cache_data["commits"]
                        elif not pushed_at:
                            return cache_data["commits"]
                    elif isinstance(cache_data, list):
                        return cache_data
            except Exception:
                pass

        commits = []
        page = 1
        while True:
            params = {
                "per_page": 100,
                "page": page
            }
            if default_branch:
                params["sha"] = default_branch
            
            resp = self._api_get(session, f"/repos/{owner}/{repo_name}/commits", params=params)
            if not resp or resp.status_code != 200:
                break
            
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            
            for c in batch:
                commit_info = {
                    "sha": c.get("sha"),
                    "message": (c.get("commit", {}).get("message") or "").split("\n")[0][:120],
                    "author_name": c.get("commit", {}).get("author", {}).get("name"),
                    "author_email": c.get("commit", {}).get("author", {}).get("email"),
                    "date": c.get("commit", {}).get("author", {}).get("date"),
                    "committer_date": c.get("commit", {}).get("committer", {}).get("date"),
                    "login": c.get("author", {}).get("login") if c.get("author") else None
                }
                commits.append(commit_info)
                
            if len(batch) < 100:
                break
            page += 1

        payload = {
            "pushed_at": pushed_at,
            "count": len(commits),
            "commits": commits
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return commits

    def fetch_all_repo_commits(self, repos, force_refresh=False, max_workers=5):
        total = len(repos)
        print(f"[开始] 开始同步 {total} 个仓库的提交记录（线程数: {max_workers}）...")
        results = {}
        completed_count = 0

        def worker(repo):
            session = self._create_session()
            owner = repo["owner"]["login"]
            name = repo["name"]
            default_branch = repo.get("default_branch")
            pushed_at = repo.get("pushed_at")
            commits = self.get_repo_commits(
                session=session,
                owner=owner,
                repo_name=name,
                default_branch=default_branch,
                pushed_at=pushed_at,
                force_refresh=force_refresh
            )
            return name, commits

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(worker, repo): repo["name"] for repo in repos}
            for future in as_completed(futures):
                name = futures[future]
                completed_count += 1
                try:
                    repo_name, commits = future.result()
                    results[repo_name] = commits
                    if completed_count % 10 == 0 or completed_count == total:
                        print(f"[进度] 已处理 {completed_count}/{total} 个仓库 ({repo_name}: {len(commits)} 提交)")
                except Exception as e:
                    print(f"[错误] 仓库 {name} 获取提交失败: {e}")
                    results[name] = []

        print(f"[完成] 所有仓库提交记录同步完毕！")
        return results
