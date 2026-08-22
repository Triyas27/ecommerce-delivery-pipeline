with orders as (
    select * from {{ ref('stg_orders') }}
    where status = 'delivered'
      and delivered_at is not null
),

customers as (
    select * from {{ ref('stg_customers') }}
),

items as (
    select * from {{ ref('int_order_items_agg') }}
),

payments as (
    select * from {{ ref('int_order_payments_agg') }}
),

distance as (
    select * from {{ ref('int_order_distance') }}
),

labeled as (
    select
        order_id,
        customer_id,
        purchased_at,
        delivered_at,
        estimated_delivery_at,
        (delivered_at > estimated_delivery_at) as is_late,
        date_diff('day', purchased_at, estimated_delivery_at) as promised_days,
        date_part('dow', purchased_at) as purchase_day_of_week,
        date_part('month', purchased_at) as purchase_month
    from orders
)

select
    labeled.order_id,
    labeled.customer_id,
    labeled.purchased_at,
    labeled.delivered_at,
    labeled.estimated_delivery_at,
    labeled.promised_days,
    labeled.purchase_day_of_week,
    labeled.purchase_month,
    labeled.is_late,

    customers.zip_code_prefix as customer_zip_code_prefix,
    customers.city as customer_city,
    customers.state as customer_state,

    items.item_count,
    items.distinct_product_count,
    items.distinct_seller_count,
    items.total_price,
    items.total_freight_value,
    items.avg_product_weight_g,
    items.max_product_volume_cm3,

    payments.payment_count,
    payments.total_payment_value,
    payments.max_installments,
    payments.primary_payment_type,

    distance.customer_seller_distance_km

from labeled
left join customers on labeled.customer_id = customers.customer_id
left join items on labeled.order_id = items.order_id
left join payments on labeled.order_id = payments.order_id
left join distance on labeled.order_id = distance.order_id
