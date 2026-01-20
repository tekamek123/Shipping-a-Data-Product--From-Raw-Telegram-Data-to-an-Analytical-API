{{ config(materialized='table') }}

with src as (
    select *
    from {{ ref('stg_telegram_messages') }}
),
with_keys as (
    select
        s.message_id,
        s.channel_name,
        s.channel_slug,
        s.message_timestamp,
        s.message_text,
        s.message_length,
        s.view_count,
        s.forward_count,
        s.has_image,
        s.has_media,
        date(s.message_timestamp) as message_date,
        cast(to_char(s.message_timestamp, 'YYYYMMDD') as int) as date_key
    from src s
    where s.message_timestamp is not null
)

select
    abs(hashtext(wk.channel_slug || '-' || wk.message_id::text)) as message_key,
    wk.message_id,
    dc.channel_key,
    dd.date_key,
    wk.message_timestamp,
    wk.message_text,
    wk.message_length,
    wk.view_count,
    wk.forward_count,
    wk.has_image,
    wk.has_media
from with_keys wk
join {{ ref('dim_channels') }} dc
  on wk.channel_slug = dc.channel_slug
join {{ ref('dim_dates') }} dd
  on wk.message_date = dd.full_date

