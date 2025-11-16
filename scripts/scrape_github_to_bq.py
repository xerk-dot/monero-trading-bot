#!/usr/bin/env python3
"""
Scrape Monero GitHub activity and write to BigQuery

This script monitors developer activity across all Monero GitHub repos
and stores the data in BigQuery for analysis and signal generation.

Usage:
    # Scrape last 24 hours
    python3 scripts/scrape_github_to_bq.py

    # Scrape last 7 days
    python3 scripts/scrape_github_to_bq.py --hours 168

    # Scrape specific repos only
    python3 scripts/scrape_github_to_bq.py --repos monero monero-gui

Requirements:
    - GitHub token (optional but recommended): GITHUB_TOKEN in .env
    - GCP credentials: GOOGLE_APPLICATION_CREDENTIALS env var or default credentials
    - GCP project ID: GCP_PROJECT_ID in .env
"""

import argparse
import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config import config
from src.strategies.experimental.github.bigquery_writer import GitHubBigQueryWriter
from src.strategies.experimental.github.github_scraper import MoneroGitHubScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def scrape_and_write_to_bq(
    hours: int = 24, repos: list = None, project_id: str = None, dataset_id: str = "monero_github"
):
    """
    Scrape GitHub activity and write to BigQuery

    Args:
        hours: Look back this many hours
        repos: List of repo names (None = priority repos)
        project_id: GCP project ID
        dataset_id: BigQuery dataset name
    """

    # Get project ID
    if not project_id:
        project_id = config.gcp_project_id or os.getenv("GCP_PROJECT_ID")

    if not project_id:
        logger.error("GCP_PROJECT_ID not found in config or environment")
        logger.error("Set it in .env file or pass --project-id argument")
        return False

    logger.info("=" * 60)
    logger.info("🔍 Monero GitHub Activity Scraper → BigQuery")
    logger.info("=" * 60)
    logger.info(f"Project: {project_id}")
    logger.info(f"Dataset: {dataset_id}")
    logger.info(f"Lookback: {hours} hours")
    logger.info("")

    # Initialize BigQuery writer
    try:
        logger.info("Initializing BigQuery writer...")
        bq_writer = GitHubBigQueryWriter(project_id=project_id, dataset_id=dataset_id)
        logger.info("✅ BigQuery writer initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize BigQuery: {e}")
        logger.error(
            "Make sure GOOGLE_APPLICATION_CREDENTIALS is set or default credentials are configured"
        )
        return False

    # Scrape GitHub
    try:
        logger.info("Initializing GitHub scraper...")
        async with MoneroGitHubScraper() as scraper:
            logger.info("✅ GitHub scraper initialized")
            logger.info("")

            # Scrape all activity
            results = await scraper.scrape_all_activity(repos=repos, since_hours=hours)

            logger.info("")
            logger.info("📊 Scraping Results:")
            logger.info(f"  Commits: {len(results['commits'])}")
            logger.info(f"  Pull Requests: {len(results['pull_requests'])}")
            logger.info(f"  Issues: {len(results['issues'])}")
            logger.info(f"  Repos: {len(results['repo_stats'])}")
            logger.info("")

            if not any([results["commits"], results["pull_requests"], results["issues"]]):
                logger.warning("⚠️  No data scraped - nothing to write to BigQuery")
                return True

            # Write to BigQuery
            logger.info("💾 Writing to BigQuery...")

            # Insert commits
            if results["commits"]:
                count = bq_writer.insert_commits(results["commits"])
                logger.info(f"  ✅ Inserted {count} commits")

            # Insert PRs
            if results["pull_requests"]:
                count = bq_writer.insert_pull_requests(results["pull_requests"])
                logger.info(f"  ✅ Inserted {count} pull requests")

            # Insert issues
            if results["issues"]:
                count = bq_writer.insert_issues(results["issues"])
                logger.info(f"  ✅ Inserted {count} issues")

            # Insert repo stats
            if results["repo_stats"]:
                count = bq_writer.insert_repo_stats(results["repo_stats"])
                logger.info(f"  ✅ Inserted {count} repo stats")

            # Calculate and insert aggregated metrics
            metrics = calculate_metrics(results)
            if bq_writer.insert_activity_metrics(metrics):
                logger.info("  ✅ Inserted activity metrics")

            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ Successfully scraped and wrote to BigQuery!")
            logger.info("=" * 60)

            return True

    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        import traceback

        traceback.print_exc()
        return False


def calculate_metrics(results: dict) -> dict:
    """Calculate aggregated activity metrics"""

    commits = results["commits"]
    prs = results["pull_requests"]
    issues = results["issues"]

    # Commit metrics
    total_commits = len(commits)
    unique_authors = len(set(c.author for c in commits))
    total_additions = sum(c.additions for c in commits)
    total_deletions = sum(c.deletions for c in commits)

    # PR metrics
    total_prs = len(prs)
    merged_prs = len([pr for pr in prs if pr.merged_at])
    open_prs = len([pr for pr in prs if pr.state == "open"])

    # Issue metrics
    total_issues = len(issues)
    closed_issues = len([i for i in issues if i.state == "closed"])
    open_issues = len([i for i in issues if i.state == "open"])

    # Engagement score (weighted combination)
    # Higher weight for merged PRs and commits
    engagement_score = (
        total_commits * 1.0
        + merged_prs * 3.0
        + open_prs * 1.5
        + closed_issues * 1.0
        + (total_additions + total_deletions) / 1000 * 2.0
    )

    return {
        "period_hours": 24,  # TODO: Make this dynamic
        "total_commits": total_commits,
        "unique_authors": unique_authors,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "open_prs": open_prs,
        "total_issues": total_issues,
        "closed_issues": closed_issues,
        "open_issues": open_issues,
        "engagement_score": engagement_score,
        "wow_change_pct": 0.0,  # TODO: Calculate from historical data
        "velocity_score": 0.0,  # TODO: Calculate from historical data
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape Monero GitHub activity to BigQuery")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument(
        "--repos", nargs="+", help="Specific repos to scrape (default: priority repos)"
    )
    parser.add_argument("--project-id", help="GCP project ID (default: from .env)")
    parser.add_argument(
        "--dataset-id", default="monero_github", help="BigQuery dataset ID (default: monero_github)"
    )

    args = parser.parse_args()

    try:
        success = asyncio.run(
            scrape_and_write_to_bq(
                hours=args.hours,
                repos=args.repos,
                project_id=args.project_id,
                dataset_id=args.dataset_id,
            )
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
