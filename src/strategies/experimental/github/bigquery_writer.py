"""
BigQuery writer for GitHub activity data
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)


class GitHubBigQueryWriter:
    """Write GitHub activity data to BigQuery"""

    def __init__(
        self, project_id: str, dataset_id: str = "monero_github", credentials_path: str = None
    ):
        """
        Initialize BigQuery writer

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset name
            credentials_path: Path to service account JSON (optional, uses default credentials if None)
        """
        self.project_id = project_id
        self.dataset_id = dataset_id

        if credentials_path:
            self.client = bigquery.Client.from_service_account_json(
                credentials_path, project=project_id
            )
        else:
            self.client = bigquery.Client(project=project_id)

        self.dataset_ref = f"{project_id}.{dataset_id}"

        # Ensure dataset exists
        self._create_dataset_if_not_exists()

        # Ensure tables exist
        self._create_tables_if_not_exist()

    def _create_dataset_if_not_exists(self):
        """Create BigQuery dataset if it doesn't exist"""
        try:
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_ref} already exists")
        except NotFound:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"
            dataset.description = "Monero GitHub activity data for trading signals"
            self.client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_ref}")

    def _create_tables_if_not_exist(self):
        """Create all required BigQuery tables"""

        # Commits table
        commits_schema = [
            bigquery.SchemaField("repo", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("sha", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("author", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("additions", "INTEGER"),
            bigquery.SchemaField("deletions", "INTEGER"),
            bigquery.SchemaField("files_changed", "INTEGER"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table_if_not_exists("commits", commits_schema)

        # Pull Requests table
        prs_schema = [
            bigquery.SchemaField("repo", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("author", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("state", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("merged_at", "TIMESTAMP"),
            bigquery.SchemaField("additions", "INTEGER"),
            bigquery.SchemaField("deletions", "INTEGER"),
            bigquery.SchemaField("comments", "INTEGER"),
            bigquery.SchemaField("body", "STRING"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table_if_not_exists("pull_requests", prs_schema)

        # Issues table
        issues_schema = [
            bigquery.SchemaField("repo", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("author", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("state", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("closed_at", "TIMESTAMP"),
            bigquery.SchemaField("comments", "INTEGER"),
            bigquery.SchemaField("labels", "STRING", mode="REPEATED"),
            bigquery.SchemaField("body", "STRING"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table_if_not_exists("issues", issues_schema)

        # Repository stats table
        repo_stats_schema = [
            bigquery.SchemaField("repo", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("stars", "INTEGER"),
            bigquery.SchemaField("forks", "INTEGER"),
            bigquery.SchemaField("watchers", "INTEGER"),
            bigquery.SchemaField("open_issues", "INTEGER"),
            bigquery.SchemaField("size_kb", "INTEGER"),
            bigquery.SchemaField("language", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
            bigquery.SchemaField("pushed_at", "TIMESTAMP"),
        ]
        self._create_table_if_not_exists("repo_stats", repo_stats_schema)

        # Activity metrics table (aggregated)
        metrics_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("period_hours", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("total_commits", "INTEGER"),
            bigquery.SchemaField("unique_authors", "INTEGER"),
            bigquery.SchemaField("total_additions", "INTEGER"),
            bigquery.SchemaField("total_deletions", "INTEGER"),
            bigquery.SchemaField("total_prs", "INTEGER"),
            bigquery.SchemaField("merged_prs", "INTEGER"),
            bigquery.SchemaField("open_prs", "INTEGER"),
            bigquery.SchemaField("total_issues", "INTEGER"),
            bigquery.SchemaField("closed_issues", "INTEGER"),
            bigquery.SchemaField("open_issues", "INTEGER"),
            bigquery.SchemaField("engagement_score", "FLOAT"),
            bigquery.SchemaField("wow_change_pct", "FLOAT"),
            bigquery.SchemaField("velocity_score", "FLOAT"),
        ]
        self._create_table_if_not_exists("activity_metrics", metrics_schema)

    def _create_table_if_not_exists(self, table_name: str, schema: list[bigquery.SchemaField]):
        """Create a BigQuery table if it doesn't exist"""
        table_ref = f"{self.dataset_ref}.{table_name}"

        try:
            self.client.get_table(table_ref)
            logger.info(f"Table {table_ref} already exists")
        except NotFound:
            table = bigquery.Table(table_ref, schema=schema)
            table = self.client.create_table(table)
            logger.info(f"Created table {table_ref}")

    def insert_commits(self, commits: list[Any]) -> int:
        """Insert commits into BigQuery"""
        if not commits:
            return 0

        table_ref = f"{self.dataset_ref}.commits"

        rows = []
        for commit in commits:
            data = asdict(commit) if hasattr(commit, "__dataclass_fields__") else commit
            rows.append(
                {
                    "repo": data["repo"],
                    "sha": data["sha"],
                    "author": data["author"],
                    "message": data["message"],
                    "timestamp": data["timestamp"].isoformat()
                    if isinstance(data["timestamp"], datetime)
                    else data["timestamp"],
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "files_changed": data.get("files_changed", 0),
                    "inserted_at": datetime.utcnow().isoformat(),
                }
            )

        errors = self.client.insert_rows_json(table_ref, rows)

        if errors:
            logger.error(f"Errors inserting commits: {errors}")
            return 0

        logger.info(f"Inserted {len(rows)} commits")
        return len(rows)

    def insert_pull_requests(self, prs: list[Any]) -> int:
        """Insert pull requests into BigQuery"""
        if not prs:
            return 0

        table_ref = f"{self.dataset_ref}.pull_requests"

        rows = []
        for pr in prs:
            data = asdict(pr) if hasattr(pr, "__dataclass_fields__") else pr
            rows.append(
                {
                    "repo": data["repo"],
                    "number": data["number"],
                    "title": data["title"],
                    "author": data["author"],
                    "state": data["state"],
                    "created_at": data["created_at"].isoformat()
                    if isinstance(data["created_at"], datetime)
                    else data["created_at"],
                    "updated_at": data["updated_at"].isoformat()
                    if isinstance(data["updated_at"], datetime)
                    else data["updated_at"],
                    "merged_at": data["merged_at"].isoformat()
                    if data.get("merged_at") and isinstance(data["merged_at"], datetime)
                    else None,
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "comments": data.get("comments", 0),
                    "body": data.get("body", ""),
                    "inserted_at": datetime.utcnow().isoformat(),
                }
            )

        errors = self.client.insert_rows_json(table_ref, rows)

        if errors:
            logger.error(f"Errors inserting PRs: {errors}")
            return 0

        logger.info(f"Inserted {len(rows)} pull requests")
        return len(rows)

    def insert_issues(self, issues: list[Any]) -> int:
        """Insert issues into BigQuery"""
        if not issues:
            return 0

        table_ref = f"{self.dataset_ref}.issues"

        rows = []
        for issue in issues:
            data = asdict(issue) if hasattr(issue, "__dataclass_fields__") else issue
            rows.append(
                {
                    "repo": data["repo"],
                    "number": data["number"],
                    "title": data["title"],
                    "author": data["author"],
                    "state": data["state"],
                    "created_at": data["created_at"].isoformat()
                    if isinstance(data["created_at"], datetime)
                    else data["created_at"],
                    "updated_at": data["updated_at"].isoformat()
                    if isinstance(data["updated_at"], datetime)
                    else data["updated_at"],
                    "closed_at": data["closed_at"].isoformat()
                    if data.get("closed_at") and isinstance(data["closed_at"], datetime)
                    else None,
                    "comments": data.get("comments", 0),
                    "labels": data.get("labels", []),
                    "body": data.get("body", ""),
                    "inserted_at": datetime.utcnow().isoformat(),
                }
            )

        errors = self.client.insert_rows_json(table_ref, rows)

        if errors:
            logger.error(f"Errors inserting issues: {errors}")
            return 0

        logger.info(f"Inserted {len(rows)} issues")
        return len(rows)

    def insert_repo_stats(self, stats: list[dict[str, Any]]) -> int:
        """Insert repository stats into BigQuery"""
        if not stats:
            return 0

        table_ref = f"{self.dataset_ref}.repo_stats"

        rows = []
        for stat in stats:
            rows.append(
                {
                    "repo": stat["repo"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "stars": stat.get("stars", 0),
                    "forks": stat.get("forks", 0),
                    "watchers": stat.get("watchers", 0),
                    "open_issues": stat.get("open_issues", 0),
                    "size_kb": stat.get("size_kb", 0),
                    "language": stat.get("language"),
                    "description": stat.get("description"),
                    "created_at": stat.get("created_at"),
                    "updated_at": stat.get("updated_at"),
                    "pushed_at": stat.get("pushed_at"),
                }
            )

        errors = self.client.insert_rows_json(table_ref, rows)

        if errors:
            logger.error(f"Errors inserting repo stats: {errors}")
            return 0

        logger.info(f"Inserted {len(rows)} repo stats")
        return len(rows)

    def insert_activity_metrics(self, metrics: dict[str, Any]) -> bool:
        """Insert aggregated activity metrics"""
        table_ref = f"{self.dataset_ref}.activity_metrics"

        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": metrics.get("period_hours", 24),
            "total_commits": metrics.get("total_commits", 0),
            "unique_authors": metrics.get("unique_authors", 0),
            "total_additions": metrics.get("total_additions", 0),
            "total_deletions": metrics.get("total_deletions", 0),
            "total_prs": metrics.get("total_prs", 0),
            "merged_prs": metrics.get("merged_prs", 0),
            "open_prs": metrics.get("open_prs", 0),
            "total_issues": metrics.get("total_issues", 0),
            "closed_issues": metrics.get("closed_issues", 0),
            "open_issues": metrics.get("open_issues", 0),
            "engagement_score": metrics.get("engagement_score", 0.0),
            "wow_change_pct": metrics.get("wow_change_pct", 0.0),
            "velocity_score": metrics.get("velocity_score", 0.0),
        }

        errors = self.client.insert_rows_json(table_ref, [row])

        if errors:
            logger.error(f"Errors inserting metrics: {errors}")
            return False

        logger.info("Inserted activity metrics")
        return True
