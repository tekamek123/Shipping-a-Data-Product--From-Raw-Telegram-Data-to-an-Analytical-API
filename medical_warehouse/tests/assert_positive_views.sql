-- Fail if any message has negative views or forward counts
select
  message_id,
  view_count,
  forward_count
from {{ ref('fct_messages') }}
where coalesce(view_count, 0) < 0
   or coalesce(forward_count, 0) < 0

