from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from dotenv import load_dotenv

# dbt writes your marts models to the `marts` schema (see `medical_warehouse/dbt_project.yml`)
# Override if needed by setting DBT_SCHEMA in your environment (.env)
load_dotenv()
# Your warehouse may be configured to prefix schemas (e.g. `raw_marts`), so default to that
# if you haven't explicitly set DBT_SCHEMA.
DBT_SCHEMA = os.getenv("DBT_SCHEMA", "raw_marts")

def get_top_products(db: Session, limit: int):
    query = text(f"""
        select
            lower(word) as term,
            count(*) as frequency
        from {DBT_SCHEMA}.fct_messages,
        regexp_split_to_table(message_text, '\\s+') as word
        where length(word) > 4
        group by term
        order by frequency desc
        limit :limit
    """)
    return db.execute(query, {"limit": limit}).mappings().all()


def get_channel_activity(db: Session, channel_name: str):
    query = text(f"""
        select
            d.full_date::text as date,
            count(*) as message_count,
            avg(f.view_count)::float as avg_views
        from {DBT_SCHEMA}.fct_messages f
        join {DBT_SCHEMA}.dim_channels c on f.channel_key = c.channel_key
        join {DBT_SCHEMA}.dim_dates d on f.date_key = d.date_key
        where c.channel_name = :channel_name
        group by d.full_date
        order by d.full_date
    """)
    return db.execute(query, {"channel_name": channel_name}).mappings().all()


def search_messages(db: Session, query_text: str, limit: int):
    query = text(f"""
        select
            f.message_id,
            c.channel_name,
            f.message_text,
            f.view_count as views
        from {DBT_SCHEMA}.fct_messages f
        join {DBT_SCHEMA}.dim_channels c on f.channel_key = c.channel_key
        where f.message_text ilike :q
        order by f.view_count desc
        limit :limit
    """)
    return db.execute(query, {"q": f"%{query_text}%", "limit": limit}).mappings().all()


def get_visual_content_stats(db: Session):
    query = text(f"""
        select
            c.channel_name,
            count(*) as total_posts,
            sum(case when f.has_image then 1 else 0 end) as image_posts,
            round(
                sum(case when f.has_image then 1 else 0 end)::numeric / count(*),
                2
            )::float as image_ratio
        from {DBT_SCHEMA}.fct_messages f
        join {DBT_SCHEMA}.dim_channels c on f.channel_key = c.channel_key
        group by c.channel_name
        order by image_ratio desc
    """)
    return db.execute(query).mappings().all()
