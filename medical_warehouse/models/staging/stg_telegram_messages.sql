{{ config(materialized='view') }}

with source as (
    select *
    from {{ source('raw', 'telegram_messages') }}
),
cleaned as (
    select
        cast(message_id as bigint) as message_id,
        channel_name,
        lower(trim(channel_name)) as channel_slug,
        cast(message_date as timestamp) as message_timestamp,
        coalesce(message_text, '') as message_text,
        length(coalesce(message_text, '')) as message_length,
        coalesce(has_media, false) as has_media,
        (coalesce(has_media, false) and image_path is not null) as has_image,
        image_path,
        cast(views as integer) as view_count,
        cast(forwards as integer) as forward_count
    from source
    where message_id is not null
      and channel_name is not null
      and coalesce(message_text, '') <> ''
)

select *
from cleaned

