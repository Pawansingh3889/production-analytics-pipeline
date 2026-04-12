# n8n Production Workflows

Visual workflow automation for the production data pipeline.

## Setup

```bash
cd n8n
docker-compose up -d
```

Open http://localhost:5678 (admin / production2026)

## Suggested Workflows

### 1. Daily Data Extraction
- Schedule: Every day at 06:00
- Steps: HTTP Request to POST /pipeline/run → Wait → Check /health → Slack/Email notification

### 2. Temperature Alert
- Schedule: Every 15 minutes
- Steps: HTTP Request to GET /temperature/breaches → If breaches found → Send alert email/Slack

### 3. Compliance Check
- Schedule: Every hour
- Steps: HTTP Request to GET /compliance/checks → Filter critical → Alert if any found

### 4. Weekly Yield Report
- Schedule: Every Monday at 08:00
- Steps: HTTP Request to GET /yield/daily?days=7 → Format as HTML table → Email to managers

### 5. Shelf Life Monitor
- Schedule: Every 4 hours
- Steps: HTTP Request to GET /shelf-life/expiring → If products approaching day 12 → Alert planner

All workflows connect to the FastAPI backend (http://localhost:8000). Build them visually in the n8n editor.
