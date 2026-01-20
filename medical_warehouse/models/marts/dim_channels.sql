{{ config(materialized='table') }}

with base as (
    select
        channel_name,
        channel_slug,
        date(message_timestamp) as message_date,
        view_count
    from {{ ref('stg_telegram_messages') }}
),
agg as (
    select
        abs(hashtext(channel_slug)) as channel_key,
        channel_name,
        channel_slug,
        case
            when channel_slug like '%lobelia%' then 'Cosmetics'
            when channel_slug like '%tikvah%' then 'Pharmaceutical'
            when channel_slug like '%chemed%' then 'Medical'
            when channel_slug like '%doctor%' then 'Medical'
            else 'Unknown'
        end as channel_type,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(view_count) as avg_views
    from base
    group by channel_name, channel_slug
)

select * from agg

