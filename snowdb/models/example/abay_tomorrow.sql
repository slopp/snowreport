
-- Use the `ref` function to select from other models

select *
from {{ ref('resort_tomorrow') }}
where resort_name = 'Arapahoe Basin'
