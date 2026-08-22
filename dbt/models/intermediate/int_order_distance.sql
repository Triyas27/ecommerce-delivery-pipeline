with orders as (
    select order_id, customer_id from {{ ref('stg_orders') }}
),

customers as (
    select customer_id, zip_code_prefix as customer_zip from {{ ref('stg_customers') }}
),

items as (
    select order_id, primary_seller_id from {{ ref('int_order_items_agg') }}
),

sellers as (
    select seller_id, zip_code_prefix as seller_zip from {{ ref('stg_sellers') }}
),

zips as (
    select orders.order_id, customer_zip, seller_zip
    from orders
    left join customers on orders.customer_id = customers.customer_id
    left join items on orders.order_id = items.order_id
    left join sellers on items.primary_seller_id = sellers.seller_id
)

select
    zips.order_id,
    {{ haversine_km('cust_geo.lat', 'cust_geo.lng', 'sell_geo.lat', 'sell_geo.lng') }} as customer_seller_distance_km
from zips
left join {{ ref('int_zip_geolocation') }} as cust_geo on zips.customer_zip = cust_geo.zip_code_prefix
left join {{ ref('int_zip_geolocation') }} as sell_geo on zips.seller_zip = sell_geo.zip_code_prefix
