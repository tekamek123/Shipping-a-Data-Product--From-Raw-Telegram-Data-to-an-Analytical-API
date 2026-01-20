# Interim Report — Medical Telegram Warehouse

Date: 2026-01-20  
Scope: Task 1 (Extract & Load) and Task 2 (Transform with dbt)

## 1) Business Objective (why we are doing this)

- Provide Kara Solutions with trusted, analysis-ready data about Ethiopian medical and cosmetics Telegram channels to answer: top-mentioned products, price/availability variation, channel media intensity, and posting trends.
- Build a modern ELT stack: raw scrape → data lake → Postgres warehouse → dbt transformations → analytics/API.
- Ensure reliability via data quality checks, reproducibility, and clear documentation.

## 2) Completed Work & Initial Analysis

### Task 1: Data Scraping & Collection

- Implemented Telegram scraper (Telethon) to pull messages, views, forwards, text, and photos.
- Images downloaded to a partitioned structure; messages persisted as JSON in a date-partitioned data lake.
- Logging to file + console to track runs and errors; re-runs are idempotent on message_id/channel.

### Task 2: Data Modeling & Transformation (dbt)

- Raw loader (`src/load_raw_to_postgres.py`) creates `raw.telegram_messages` and bulk-loads JSON.
- dbt project `medical_warehouse` with staging and marts:
  - **Staging:** `stg_telegram_messages` cleans types, drops empty text, adds `message_length`, `has_image`, normalized `channel_slug`.
  - **Marts:** star schema with `dim_channels`, `dim_dates`, `fct_messages` (one row per message, measures + media flags).
- Data tests:
  - Generic: `unique`/`not_null` on keys; `relationships` FKs.
  - Custom: `assert_no_future_messages`, `assert_positive_views`.
- Documentation hooks in `schema.yml`; ready for `dbt docs generate`.

### Initial Analysis (qualitative)

- Pipeline is ready to compute: posting volume by channel/date, engagement (views/forwards) by channel, and media prevalence. Quantitative results depend on loading the latest scrape into Postgres and running `dbt run` + `dbt test`.

## 3) Data Lake Structure (raw zone)

- Base: `data/raw/`
  - Messages (JSON, partitioned by date): `data/raw/telegram_messages/YYYY-MM-DD/<channel>.json`
    - Fields preserved: `message_id`, `channel_name`, `message_date`, `message_text`, `has_media`, `image_path`, `views`, `forwards`, full `raw_json`.
  - Images: `data/raw/images/<channel_name>/<message_id>.jpg`
  - Logs: `logs/scraper_YYYYMMDD_HHMMSS.log` (run activity, errors, channels scraped).

## 4) Star Schema Diagram (warehouse)

```
        dim_channels                     dim_dates
    +-----------------+             +-----------------+
    | channel_key (PK)|             | date_key (PK)   |
    | channel_name    |             | full_date       |
    | channel_slug    |             | day_of_week     |
    | channel_type    |             | week_of_year    |
    | first_post_date |             | month/quarter   |
    | last_post_date  |             | year            |
    | total_posts     |             | is_weekend      |
    | avg_views       |             +-----------------+
    +-----------------+
             \                         /
              \                       /
               \                     /
                 +-----------------+
                 |   fct_messages  |
                 | message_key (PK)|
                 | message_id      |
                 | channel_key (FK)|
                 | date_key (FK)   |
                 | message_ts      |
                 | message_text    |
                 | message_length  |
                 | view_count      |
                 | forward_count   |
                 | has_image       |
                 | has_media       |
                 +-----------------+
```

## 5) Data Quality Issues & Resolutions

- Empty or null message_text: filtered out in staging (`where ... <> ''`).
- Missing message_id/channel_name: excluded in staging and loader.
- Timestamp parsing errors: guarded; invalid dates dropped in staging; custom test prevents future dates.
- Duplicates: loader upserts on `(message_id, channel_name)`; staging dedup implicitly via source uniqueness.
- Negative views/forwards: custom test `assert_positive_views` fails if found.
- Inconsistent channel naming: normalized `channel_slug` (lower/trim, safe join key) and hashed surrogate keys.
- Missing images: `has_media` vs `has_image` derived separately; safe to count media presence without file dependence.

## 6) Next Steps & Key Focus

- Run end-to-end: load latest JSON into Postgres, then `dbt run && dbt test` to validate model outputs.
- Automate orchestration (Dagster) for scheduled scrapes and dbt runs.
- Add YOLO enrichment to tag image content and extend fact table with detected product classes.
- Build FastAPI analytical endpoints on top of marts (top products, engagement trends, media intensity by channel).
- Add volume/engagement dashboards once marts are populated.

## 7) How to Reproduce (quick commands)

```pwsh
# From repo root
python -m pip install --upgrade pip
pip install -r requirements.txt

# DB env vars (example)
$env:DB_HOST="localhost"; $env:DB_PORT="5432"
$env:DB_NAME="telegram_warehouse"; $env:DB_USER="postgres"
$env:DB_PASSWORD="software"; $env:DB_SCHEMA="raw"

# Load raw -> Postgres
python src/load_raw_to_postgres.py

# dbt (uses profiles.yml in repo root if present)
dbt run  --project-dir medical_warehouse --profiles-dir .
dbt test --project-dir medical_warehouse --profiles-dir .
dbt docs generate
```

---
