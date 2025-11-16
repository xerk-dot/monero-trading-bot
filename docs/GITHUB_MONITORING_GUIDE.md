# GitHub Activity Monitoring for XMR Trading

## Overview

Monitor developer activity across all Monero GitHub repositories as a leading indicator for price action. Developer activity (commits, PRs, issues) often precedes:
- Major releases
- Protocol upgrades
- Feature launches
- Ecosystem improvements

All signals price-positive catalysts for XMR.

## Why This Works

**Developer Activity → Price Action**

1. **Increased commits** = Active development → upcoming features
2. **Merged PRs** = Real progress → near-term releases
3. **Issue velocity** = Community engagement → ecosystem health
4. **Contributor growth** = Network effects → long-term value

Much more reliable than darknet scraping:
- ✅ Legal and ethical
- ✅ Free (5000 requests/hour with token)
- ✅ Real-time data
- ✅ No Tor required
- ✅ Historical data available

## Architecture

```
GitHub API → Scraper → BigQuery → Strategy → Trading Signals
```

### Data Collected

**Commits:**
- SHA, author, message, timestamp
- Additions/deletions, files changed
- Stored in: `{project}.monero_github.commits`

**Pull Requests:**
- Number, title, author, state
- Created/updated/merged timestamps
- Code changes, comments, description
- Stored in: `{project}.monero_github.pull_requests`

**Issues:**
- Number, title, author, state
- Created/updated/closed timestamps
- Comments, labels, description
- Stored in: `{project}.monero_github.issues`

**Repository Stats:**
- Stars, forks, watchers
- Open issues count
- Last push timestamp
- Stored in: `{project}.monero_github.repo_stats`

**Aggregated Metrics:**
- Total commits, unique authors
- PR merge rate, issue closure rate
- Engagement score (weighted combination)
- Week-over-week change %
- Velocity trend
- Stored in: `{project}.monero_github.activity_metrics`

## Setup

### 1. Get GitHub Token (Optional but Recommended)

**Without token:** 60 requests/hour (might hit limits)
**With token:** 5,000 requests/hour (recommended)

**Create token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "XMR Trading Bot"
4. Scopes: Select `public_repo` (read-only access to public repos)
5. Click "Generate token"
6. Copy the token (you won't see it again)

### 2. Setup Google Cloud Platform

**Create project:**
```bash
# 1. Go to https://console.cloud.google.com
# 2. Create new project (e.g., "xmr-trading-bot")
# 3. Note the Project ID
```

**Enable BigQuery API:**
```bash
# 1. Go to APIs & Services → Library
# 2. Search "BigQuery API"
# 3. Click "Enable"
```

**Create service account:**
```bash
# 1. Go to IAM & Admin → Service Accounts
# 2. Click "Create Service Account"
# 3. Name: "github-scraper"
# 4. Grant role: "BigQuery Admin"
# 5. Click "Done"
# 6. Click on the service account
# 7. Go to "Keys" tab
# 8. Add Key → Create new key → JSON
# 9. Download the JSON file
# 10. Save it securely (e.g., ~/.config/gcp/xmr-trading-bot.json)
```

### 3. Configure `.env`

```bash
# GitHub (optional but recommended)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# GCP/BigQuery (required)
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Or set credentials path in .env
GCP_CREDENTIALS_PATH=/path/to/service-account-key.json

# GitHub monitoring settings
GITHUB_MONITORING_ENABLED=true
GITHUB_SCRAPE_INTERVAL_HOURS=6
GITHUB_STRATEGY_WEIGHT=0.15
```

### 4. Install Dependencies

```bash
pip install google-cloud-bigquery==3.14.1
```

## Usage

### Manual Scraping

```bash
# Scrape last 24 hours (default)
python3 scripts/scrape_github_to_bq.py

# Scrape last 7 days
python3 scripts/scrape_github_to_bq.py --hours 168

# Scrape specific repos only
python3 scripts/scrape_github_to_bq.py --repos monero monero-gui

# Use custom project/dataset
python3 scripts/scrape_github_to_bq.py --project-id my-project --dataset-id custom_dataset
```

### Automated Scraping (Cron)

```bash
# Add to crontab for every 6 hours
crontab -e

# Add this line:
0 */6 * * * cd /path/to/repo && python3 scripts/scrape_github_to_bq.py >> logs/github_scraper.log 2>&1
```

## Querying BigQuery

### Recent Activity

```sql
-- Commits in last 24 hours
SELECT
  repo,
  COUNT(*) as commit_count,
  COUNT(DISTINCT author) as unique_authors,
  SUM(additions + deletions) as total_changes
FROM `{project}.monero_github.commits`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY repo
ORDER BY commit_count DESC;
```

### PR Velocity

```sql
-- Merged PRs in last week
SELECT
  repo,
  COUNT(*) as merged_count,
  AVG(TIMESTAMP_DIFF(merged_at, created_at, HOUR)) as avg_time_to_merge_hours
FROM `{project}.monero_github.pull_requests`
WHERE merged_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY repo
ORDER BY merged_count DESC;
```

### Top Contributors

```sql
-- Most active developers this month
SELECT
  author,
  COUNT(*) as commits,
  SUM(additions) as lines_added,
  COUNT(DISTINCT repo) as repos_contributed
FROM `{project}.monero_github.commits`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY author
ORDER BY commits DESC
LIMIT 20;
```

### Engagement Trends

```sql
-- Week-over-week activity comparison
WITH this_week AS (
  SELECT COUNT(*) as count
  FROM `{project}.monero_github.commits`
  WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
),
last_week AS (
  SELECT COUNT(*) as count
  FROM `{project}.monero_github.commits`
  WHERE timestamp BETWEEN
    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
    AND TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
)
SELECT
  this_week.count as this_week_commits,
  last_week.count as last_week_commits,
  ROUND((this_week.count - last_week.count) / last_week.count * 100, 2) as wow_change_pct
FROM this_week, last_week;
```

## Signal Generation Strategy

### Bullish Signals

- **Commit surge**: >50% increase WoW
- **PR merges**: >10 merged PRs in 24h
- **New contributors**: >5 new unique authors in week
- **High engagement**: Engagement score >100

### Bearish Signals

- **Activity drought**: <50% of normal commit rate
- **Stalled PRs**: Open PRs aging >30 days
- **Issue buildup**: Open issues increasing >20% WoW

### Signal Strength Calculation

```python
strength = (
    commit_score * 0.3 +
    pr_score * 0.4 +
    issue_score * 0.2 +
    contributor_score * 0.1
)
```

## Cost Breakdown

- **GitHub API**: Free (with 5K requests/hour limit)
- **BigQuery Storage**: ~$0.02/GB/month (first 10GB free)
- **BigQuery Queries**: First 1TB/month free
- **Expected monthly cost**: $0-5 depending on usage

For this use case, you'll likely stay in the free tier.

## Troubleshooting

### "Rate limit exceeded"
- Get a GitHub token (increases from 60 to 5000 requests/hour)
- Add delays between requests (already implemented)

### "Permission denied" on BigQuery
- Check service account has "BigQuery Admin" role
- Verify GOOGLE_APPLICATION_CREDENTIALS points to correct JSON file

### "Dataset not found"
- Script auto-creates dataset on first run
- Check GCP_PROJECT_ID is correct
- Verify BigQuery API is enabled in GCP console

### No data scraped
- Check GitHub repos exist and are public
- Verify time range has activity (try larger `--hours` value)
- Check GitHub token is valid (if using one)

## Next Steps

1. Run initial scrape to populate historical data:
   ```bash
   python3 scripts/scrape_github_to_bq.py --hours 720  # 30 days
   ```

2. Set up cron job for automated scraping

3. Build dashboards in BigQuery or connect to Data Studio

4. Integrate with trading strategy (coming soon)

## Resources

- GitHub API Docs: https://docs.github.com/en/rest
- BigQuery Docs: https://cloud.google.com/bigquery/docs
- Monero GitHub: https://github.com/monero-project
