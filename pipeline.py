"""
Dagster orchestration for the medical Telegram data pipeline.

This job wires together the main steps:
  1. scrape_telegram_data      – collect new JSON data from Telegram (placeholder hook)
  2. load_raw_to_postgres      – load JSON files into Postgres raw layer
  3. run_dbt_transformations   – build dbt models (staging + marts)
  4. run_yolo_enrichment       – run YOLOv8 image enrichment

Run locally:
  1) Install deps:  pip install -r requirements.txt
  2) Start Dagster UI from repo root:
         dagster dev -f pipeline.py
  3) Open http://localhost:3000, find job `medical_telegram_pipeline`, and launch a run.
"""

import subprocess
from pathlib import Path

from dagster import (
    Definitions,
    In,
    JobDefinition,
    Out,
    ScheduleDefinition,
    job,
    op,
)


REPO_ROOT = Path(__file__).resolve().parent


@op(
    out=Out(str, description="Path to the folder where scraped Telegram JSON files live."),
    description=(
        "Scrape Telegram messages into the data lake.\n\n"
        "NOTE: This is a placeholder hook. Wire this to your real scraper script or "
        "Telethon-based code when ready."
    ),
)
def scrape_telegram_data(context) -> str:
    data_dir = REPO_ROOT / "data" / "raw" / "telegram_messages"
    data_dir.mkdir(parents=True, exist_ok=True)

    # TODO: replace this placeholder with a real scraper invocation, e.g.:
    # subprocess.run(
    #     ["python", "src/telegram_scraper.py"],
    #     cwd=REPO_ROOT,
    #     check=True,
    # )

    context.log.info(f"(placeholder) Skipping real scraping step. Using existing data in {data_dir}")
    return str(data_dir)


@op(
    ins={"_input": In(str, description="Output from scrape_telegram_data (unused, just for ordering).")},
    description="Load raw Telegram JSON files from data lake into Postgres `raw.telegram_messages`.",
    out=Out(str, description="A simple marker passed to downstream ops to enforce ordering."),
)
def load_raw_to_postgres(context, _input: str) -> None:
    context.log.info("Running loader: src/load_raw_to_postgres.py")
    subprocess.run(
        ["python", "src/load_raw_to_postgres.py"],
        cwd=REPO_ROOT,
        check=True,
    )
    return "raw_loaded"


@op(
    description="Run dbt models (staging + marts) inside the medical_warehouse dbt project.",
    ins={"_input": In(str, description="Marker to enforce upstream ordering.")},
    out=Out(str, description="A simple marker passed to downstream ops to enforce ordering."),
)
def run_dbt_transformations(context, _input: str) -> str:
    dbt_project_dir = REPO_ROOT / "medical_warehouse"
    context.log.info(f"Running dbt from {dbt_project_dir}")

    # dbt run
    subprocess.run(
        ["dbt", "run"],
        cwd=str(dbt_project_dir),
        check=True,
    )

    # Optionally, run tests as part of the pipeline
    subprocess.run(
        ["dbt", "test"],
        cwd=str(dbt_project_dir),
        check=True,
    )
    return "dbt_done"


@op(
    description=(
        "Run YOLOv8 image enrichment over images under data/raw/images and "
        "write detections to data/processed/yolo_detections.csv."
    ),
    ins={"_input": In(str, description="Marker to enforce upstream ordering.")},
)
def run_yolo_enrichment(context, _input: str) -> None:
    context.log.info("Running YOLO enrichment: src/yolo_detect.py")
    subprocess.run(
        ["python", "src/yolo_detect.py"],
        cwd=REPO_ROOT,
        check=True,
    )


@job(description="End-to-end medical Telegram analytics pipeline.")
def medical_telegram_pipeline() -> None:
    """
    Full pipeline:
      scrape_telegram_data -> load_raw_to_postgres -> run_dbt_transformations -> run_yolo_enrichment
    """
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(scraped)
    dbt_done = run_dbt_transformations.alias("run_dbt")(loaded)
    run_yolo_enrichment(dbt_done)


# Daily schedule at 02:00 server time
daily_medical_pipeline = ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 2 * * *",
    execution_timezone="UTC",
    name="daily_medical_telegram_pipeline",
)


defs = Definitions(
    jobs=[medical_telegram_pipeline],  # type: ignore[arg-type]
    schedules=[daily_medical_pipeline],
)


