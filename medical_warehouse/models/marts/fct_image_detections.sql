with detections as (

    select
        message_id::bigint,
        channel_name,
        image_category,
        confidence_score::float
    from {{ source('raw', 'yolo_detections') }}

),

messages as (

    select
        f.message_id,
        f.channel_key,
        f.date_key
    from {{ ref('fct_messages') }} f

),

final as (

    select
        m.message_id,
        m.channel_key,
        m.date_key,
        d.image_category,
        d.confidence_score
    from detections d
    join messages m
      on d.message_id = m.message_id

)

select * from final
