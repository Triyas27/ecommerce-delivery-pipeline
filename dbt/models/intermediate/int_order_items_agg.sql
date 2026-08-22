with items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

items_with_products as (
    select
        items.order_id,
        items.product_id,
        items.seller_id,
        items.price,
        items.freight_value,
        products.weight_g,
        products.length_cm,
        products.height_cm,
        products.width_cm
    from items
    left join products on items.product_id = products.product_id
)

select
    order_id,
    count(*) as item_count,
    count(distinct product_id) as distinct_product_count,
    count(distinct seller_id) as distinct_seller_count,
    sum(price) as total_price,
    sum(freight_value) as total_freight_value,
    avg(weight_g) as avg_product_weight_g,
    max(length_cm * height_cm * width_cm) as max_product_volume_cm3
from items_with_products
group by order_id
