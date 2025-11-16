"""
GitHub Activity Scraper for Monero Project

Monitors developer activity across all Monero GitHub repositories:
- Commits
- Pull Requests
- Issues
- Discussions
- Code contributions

Thesis: Increased developer activity correlates with upcoming releases,
feature improvements, and community engagement - all potential price catalysts.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp

from config.config import config

logger = logging.getLogger(__name__)


@dataclass
class GitHubCommit:
    """GitHub commit data"""

    repo: str
    sha: str
    author: str
    message: str
    timestamp: datetime
    additions: int
    deletions: int
    files_changed: int


@dataclass
class GitHubPullRequest:
    """GitHub pull request data"""

    repo: str
    number: int
    title: str
    author: str
    state: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    additions: int
    deletions: int
    comments: int
    body: Optional[str]


@dataclass
class GitHubIssue:
    """GitHub issue data"""

    repo: str
    number: int
    title: str
    author: str
    state: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    comments: int
    labels: list[str]
    body: Optional[str]


@dataclass
class GitHubDiscussion:
    """GitHub discussion data"""

    repo: str
    number: int
    title: str
    author: str
    created_at: datetime
    updated_at: datetime
    comments: int
    category: str
    body: Optional[str]


class MoneroGitHubScraper:
    """Scrape GitHub activity for Monero project"""

    ORG_NAME = "monero-project"

    # Priority repositories to monitor
    PRIORITY_REPOS = [
        "monero",  # Core daemon
        "monero-gui",  # GUI wallet
        "monero-site",  # Website
        "research-lab",  # Research
        "meta",  # Governance
    ]

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub scraper

        Args:
            github_token: GitHub personal access token (optional but recommended)
                         Without token: 60 requests/hour
                         With token: 5000 requests/hour
        """
        self.github_token = github_token or config.github_token
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "XMR-Darknet-Edge-Bot"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make GET request to GitHub API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")

        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403:
                    logger.warning("GitHub API rate limit exceeded")
                    return None
                elif response.status == 404:
                    logger.warning(f"GitHub endpoint not found: {endpoint}")
                    return None
                else:
                    logger.error(f"GitHub API error {response.status}: {await response.text()}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API request failed: {e}")
            return None

    async def get_organization_repos(self) -> list[str]:
        """Get all repository names in the Monero organization"""
        repos = []
        page = 1
        per_page = 100

        while True:
            data = await self._get(
                f"orgs/{self.ORG_NAME}/repos", params={"page": page, "per_page": per_page}
            )

            if not data:
                break

            repos.extend([repo["name"] for repo in data])

            if len(data) < per_page:
                break

            page += 1

        logger.info(f"Found {len(repos)} repositories in {self.ORG_NAME}")
        return repos

    async def get_commits(
        self, repo: str, since: Optional[datetime] = None, limit: int = 100
    ) -> list[GitHubCommit]:
        """Get recent commits for a repository"""
        params = {"per_page": limit}
        if since:
            params["since"] = since.isoformat()

        data = await self._get(f"repos/{self.ORG_NAME}/{repo}/commits", params=params)

        if not data:
            return []

        commits = []
        for item in data:
            try:
                commit = GitHubCommit(
                    repo=repo,
                    sha=item["sha"],
                    author=item["commit"]["author"]["name"],
                    message=item["commit"]["message"],
                    timestamp=datetime.fromisoformat(
                        item["commit"]["author"]["date"].replace("Z", "+00:00")
                    ),
                    additions=item.get("stats", {}).get("additions", 0),
                    deletions=item.get("stats", {}).get("deletions", 0),
                    files_changed=len(item.get("files", [])),
                )
                commits.append(commit)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse commit {item.get('sha')}: {e}")
                continue

        return commits

    async def get_pull_requests(
        self, repo: str, state: str = "all", limit: int = 100
    ) -> list[GitHubPullRequest]:
        """Get pull requests for a repository"""
        data = await self._get(
            f"repos/{self.ORG_NAME}/{repo}/pulls",
            params={"state": state, "per_page": limit, "sort": "updated"},
        )

        if not data:
            return []

        prs = []
        for item in data:
            try:
                pr = GitHubPullRequest(
                    repo=repo,
                    number=item["number"],
                    title=item["title"],
                    author=item["user"]["login"],
                    state=item["state"],
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                    merged_at=datetime.fromisoformat(item["merged_at"].replace("Z", "+00:00"))
                    if item.get("merged_at")
                    else None,
                    additions=item.get("additions", 0),
                    deletions=item.get("deletions", 0),
                    comments=item.get("comments", 0),
                    body=item.get("body", "")[:1000],  # Limit body length
                )
                prs.append(pr)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse PR #{item.get('number')}: {e}")
                continue

        return prs

    async def get_issues(
        self, repo: str, state: str = "all", limit: int = 100
    ) -> list[GitHubIssue]:
        """Get issues for a repository"""
        data = await self._get(
            f"repos/{self.ORG_NAME}/{repo}/issues",
            params={"state": state, "per_page": limit, "sort": "updated"},
        )

        if not data:
            return []

        issues = []
        for item in data:
            # Skip pull requests (they show up in issues endpoint too)
            if "pull_request" in item:
                continue

            try:
                issue = GitHubIssue(
                    repo=repo,
                    number=item["number"],
                    title=item["title"],
                    author=item["user"]["login"],
                    state=item["state"],
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                    closed_at=datetime.fromisoformat(item["closed_at"].replace("Z", "+00:00"))
                    if item.get("closed_at")
                    else None,
                    comments=item.get("comments", 0),
                    labels=[label["name"] for label in item.get("labels", [])],
                    body=item.get("body", "")[:1000],  # Limit body length
                )
                issues.append(issue)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse issue #{item.get('number')}: {e}")
                continue

        return issues

    async def get_repo_stats(self, repo: str) -> dict[str, Any]:
        """Get repository statistics"""
        data = await self._get(f"repos/{self.ORG_NAME}/{repo}")

        if not data:
            return {}

        return {
            "repo": repo,
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "size_kb": data.get("size", 0),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
            "language": data.get("language"),
            "description": data.get("description"),
        }

    async def get_contributors(self, repo: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get top contributors for a repository"""
        data = await self._get(
            f"repos/{self.ORG_NAME}/{repo}/contributors", params={"per_page": limit}
        )

        if not data:
            return []

        return [
            {
                "username": contributor["login"],
                "contributions": contributor["contributions"],
                "profile_url": contributor["html_url"],
            }
            for contributor in data
        ]

    async def scrape_all_activity(
        self, repos: Optional[list[str]] = None, since_hours: int = 24
    ) -> dict[str, Any]:
        """
        Scrape all activity across specified repos

        Args:
            repos: List of repo names (defaults to PRIORITY_REPOS)
            since_hours: Look back this many hours

        Returns:
            Dictionary with all scraped data
        """
        if repos is None:
            repos = self.PRIORITY_REPOS

        since = datetime.utcnow() - timedelta(hours=since_hours)

        logger.info(f"Scraping GitHub activity for {len(repos)} repos since {since_hours}h ago")

        results = {
            "timestamp": datetime.utcnow(),
            "repos_scraped": repos,
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "repo_stats": [],
        }

        for repo in repos:
            logger.info(f"Scraping {repo}...")

            # Get commits
            commits = await self.get_commits(repo, since=since)
            results["commits"].extend(commits)

            # Get recent PRs
            prs = await self.get_pull_requests(repo, state="all", limit=50)
            results["pull_requests"].extend(prs)

            # Get recent issues
            issues = await self.get_issues(repo, state="all", limit=50)
            results["issues"].extend(issues)

            # Get repo stats
            stats = await self.get_repo_stats(repo)
            if stats:
                results["repo_stats"].append(stats)

            # Rate limit protection
            await asyncio.sleep(0.5)

        logger.info(
            f"Scraped {len(results['commits'])} commits, "
            f"{len(results['pull_requests'])} PRs, "
            f"{len(results['issues'])} issues"
        )

        return results
