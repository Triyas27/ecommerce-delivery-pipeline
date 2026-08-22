with payments as (
    select * from {{ ref('stg_order_payments') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by order_id
            order by payment_value desc
        ) as payment_rank
    from payments
),

primary_payment as (
    select
        order_id,
        payment_type as primary_payment_type
    from ranked
    where payment_rank = 1
),

agg as (
    select
        order_id,
        count(*) as payment_count,
        sum(payment_value) as total_payment_value,
        max(payment_installments) as max_installments
    from payments
    group by order_id
)

select
    agg.order_id,
    agg.payment_count,
    agg.total_payment_value,
    agg.max_installments,
    primary_payment.primary_payment_type
from agg
left join primary_payment on agg.order_id = primary_payment.order_id
