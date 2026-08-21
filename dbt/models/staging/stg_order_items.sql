select
    order_id,
    order_item_id as item_number,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
from {{ source('raw', 'raw_order_items') }}
