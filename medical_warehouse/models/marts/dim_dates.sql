{{ config(materialized='table') }}

with dates as (
    select distinct date(message_timestamp) as full_date
    from {{ ref('stg_telegram_messages') }}
    where message_timestamp is not null
),
final as (
    select
        cast(to_char(full_date, 'YYYYMMDD') as int) as date_key,
        full_date,
        extract(dow from full_date) as day_of_week,
        to_char(full_date, 'Day') as day_name,
        extract(week from full_date) as week_of_year,
        extract(month from full_date) as month,
        to_char(full_date, 'Month') as month_name,
        extract(quarter from full_date) as quarter,
        extract(year from full_date) as year,
        case when extract(dow from full_date) in (0,6) then true else false end as is_weekend
    from dates
)

select * from final

