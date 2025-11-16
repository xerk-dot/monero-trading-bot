"""
Database models for GitHub activity storage
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GitHubCommit(Base):
    """Store GitHub commits"""

    __tablename__ = "github_commits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo = Column(String(100), nullable=False, index=True)
    sha = Column(String(40), unique=True, nullable=False, index=True)
    author = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class GitHubPullRequest(Base):
    """Store GitHub pull requests"""

    __tablename__ = "github_pull_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo = Column(String(100), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(100), nullable=False)
    state = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False, index=True)
    merged_at = Column(DateTime, nullable=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    body = Column(Text, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = {"sqlite_autoincrement": True}


class GitHubIssue(Base):
    """Store GitHub issues"""

    __tablename__ = "github_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo = Column(String(100), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(100), nullable=False)
    state = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False, index=True)
    closed_at = Column(DateTime, nullable=True)
    comments = Column(Integer, default=0)
    labels = Column(JSON, nullable=True)
    body = Column(Text, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class GitHubRepoStats(Base):
    """Store repository statistics snapshots"""

    __tablename__ = "github_repo_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    size_kb = Column(Integer, default=0)
    language = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)


class GitHubActivityMetrics(Base):
    """Store aggregated activity metrics for signal generation"""

    __tablename__ = "github_activity_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    period_hours = Column(Integer, default=24)

    # Commit metrics
    total_commits = Column(Integer, default=0)
    unique_authors = Column(Integer, default=0)
    total_additions = Column(Integer, default=0)
    total_deletions = Column(Integer, default=0)

    # PR metrics
    total_prs = Column(Integer, default=0)
    merged_prs = Column(Integer, default=0)
    open_prs = Column(Integer, default=0)

    # Issue metrics
    total_issues = Column(Integer, default=0)
    closed_issues = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)

    # Engagement score (weighted combination)
    engagement_score = Column(Float, default=0.0)

    # Week-over-week change
    wow_change_pct = Column(Float, default=0.0)

    # Activity velocity (trend)
    velocity_score = Column(Float, default=0.0)
