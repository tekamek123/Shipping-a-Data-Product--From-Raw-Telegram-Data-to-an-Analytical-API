# Medical Telegram Warehouse

An end-to-end data pipeline for Telegram, leveraging dbt for transformation, Dagster for orchestration, and YOLOv8 for data enrichment.

## Overview

### Business Need

You are a Data Engineer at Kara Solutions, a leading data science consultancy in Ethiopia. Your team has been tasked with building a robust data platform that generates actionable insights about Ethiopian medical businesses, using data scraped from public Telegram channels.

A well-designed data platform significantly enhances data analysis. To achieve this, you will build an end-to-end pipeline that answers key business questions such as:

- What are the top 10 most frequently mentioned medical products or drugs across all channels?
- How does the price or availability of a specific product vary across different channels?
- Which channels have the most visual content (e.g., images of pills vs. creams)?
- What are the daily and weekly trends in posting volume for health-related topics?

To answer these questions, you will implement a modern ELT (Extract, Load, Transform) framework. Raw data will be extracted from Telegram and loaded into a "Data Lake" storage zone. From there, it will be loaded into a PostgreSQL database, which will serve as your data warehouse. The crucial transformation step will happen inside the warehouse using dbt, where you will clean the data and remodel it into a dimensional star schema optimized for analytical queries. This layered approach ensures your data is reliable, scalable, and ready for analysis.

This project involves scraping, data modeling, object detection with YOLO to enrich the data, and exposing the final insights through an analytical API.

## Project Goals

Your job is to build a data product that does the following:

1. Develop a reproducible project environment and secure pipeline.
2. Develop a data scraping and collection pipeline to populate a raw data lake.
3. Design and implement a dimensional data model (star schema) in a PostgreSQL data warehouse.
4. Develop a data cleaning and transformation pipeline using dbt.
5. Enrich the data using object detection on images with YOLO.
6. Expose the final, cleaned data through an analytical API using FastAPI.

## Data and Features

### Telegram Channels to Scrape

- **CheMed Telegram Channel** (https://t.me/CheMed123) - Medical products
- **Lobelia Cosmetics** (https://t.me/lobelia4cosmetics) - Cosmetics and health products
- **Tikvah Pharma** (https://t.me/tikvahpharma) - Pharmaceuticals
- **Additional channels** from et.tgstat.com/medicine:
  - https://t.me/Thequorachannel
  - https://t.me/tenamereja
  - https://t.me/newoptics

### Data Fields You Will Collect

- `message_id` - Unique identifier for each message
- `channel_name` - Name of the Telegram channel
- `message_date` - Timestamp of the message
- `message_text` - Full text content (product names, prices, descriptions)
- `has_media` - Whether the message contains media
- `image_path` - Path to downloaded image (if applicable)
- `views` - Number of views on the message
- `forwards` - Number of times the message was forwarded

## Learning Outcomes

### Skills

- Telegram API data extraction using Telethon
- Data Modeling: Designing and implementing a Star Schema
- ELT Pipeline Development: Building layered data pipelines (Raw -> Staging -> Marts)
- Infrastructure as Code (IaC) and environment management using Docker and requirements.txt
- Data Transformation at scale using dbt (Data Build Tool)
- Data Enrichment using Object Detection (YOLO)
- Analytical API Development with FastAPI
- Data Pipeline Orchestration with Dagster
- Testing and validation of data systems
- Managing credentials and secrets using environment variables

### Knowledge

- Principles of modern ELT vs. ETL architectures
- Layered data architecture (Data Lake, Staging, Data Marts)
- Best practices in data cleaning, validation, and transformation
- Structuring data for efficient analytical queries (Dimensional Modeling)
- Integrating unstructured data (like image detection results) into a structured warehouse
- Best practices for deploying and maintaining reproducible data pipelines

### Communication

- Documenting data architecture and modeling decisions
- Reporting on project outcomes and technical challenges

## Communication & Support

- **Slack channel**: #all-week8
- **Office hours**: Mon–Fri, 08:00–15:00 UTC

## Project Structure

```
medical-telegram-warehouse/
├── .vscode/
│   └── settings.json
├── .github/
│   └── workflows/
│       └── unittests.yml
├── .env               # Secrets (API keys, DB passwords) - DO NOT COMMIT
├── .gitignore
├── docker-compose.yml  # Container orchestration
├── Dockerfile          # Python environment
├── requirements.txt
├── README.md
├── data/
├── medical_warehouse/            # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── tests/
├── src/
├── api/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── database.py               # Database connection
│   └── schemas.py                # Pydantic models
├── notebooks/
│   ├── __init__.py
├── tests/
│   └── __init__.py
└── scripts/
```

## Data Modeling & Transformation (Task 2)

### Prerequisites
- PostgreSQL running and accessible
- Populate `.env` from `env.template` with DB settings (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SCHEMA`)
- Install dependencies: `pip install -r requirements.txt`

### Load Raw Data to PostgreSQL
1. Ensure scraped JSON lives under `data/raw/telegram_messages/YYYY-MM-DD/*.json`.
2. Run the loader to create `raw.telegram_messages` and insert data:
   ```bash
   python src/load_raw_to_postgres.py
   ```

### dbt Setup
1. Copy `medical_warehouse/profiles-template.yml` to your dbt profiles location (e.g., `~/.dbt/profiles.yml`) and adjust credentials or rely on environment variables.
2. From repo root, run:
   ```bash
   dbt run         # builds staging + marts
   dbt test        # runs generic + custom tests
   dbt docs generate
   dbt docs serve  # optional local docs site
   ```

### Star Schema Design
- **dim_channels**: one row per channel; surrogate `channel_key` from channel slug; includes type classification, first/last post dates, total posts, avg views.
- **dim_dates**: canonical calendar dimension (YYYYMMDD keys) with day/week/month/quarter/year flags and weekend flag.
- **fct_messages**: one row per message; links to `dim_channels` and `dim_dates`; measures include views, forwards, message length, and media flags.

### Data Quality Tests
- Generic dbt tests: `unique`/`not_null` on keys; `relationships` on FKs.
- Custom tests:
  - `assert_no_future_messages.sql`: prevents timestamps beyond current_date.
  - `assert_positive_views.sql`: enforces non-negative views/forwards.

## Getting Started

_Instructions will be added as the project progresses._

## License

_To be determined_
