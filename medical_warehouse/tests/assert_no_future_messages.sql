-- Fail if any messages have a timestamp in the future
select
  message_id,
  message_timestamp
from {{ ref('fct_messages') }}
where message_timestamp::date > current_date

