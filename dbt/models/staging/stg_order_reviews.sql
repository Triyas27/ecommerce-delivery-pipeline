select
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date as created_at,
    review_answer_timestamp as answered_at
from {{ source('raw', 'raw_order_reviews') }}
