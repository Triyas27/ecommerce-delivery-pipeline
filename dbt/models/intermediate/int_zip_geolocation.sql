select
    zip_code_prefix,
    avg(lat) as lat,
    avg(lng) as lng
from {{ ref('stg_geolocation') }}
group by zip_code_prefix
