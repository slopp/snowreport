
/*
    Welcome to your first dbt model!
    Did you know that you can also configure models directly within SQL files?
    This will override configurations stated in dbt_project.yml

    Try changing "table" to "view" below
*/

{{ config(materialized='table') }}

select resort_name, condition_tomorrow, low_tomorrow, high_tomorrow
from {{ source('snocountry', 'resort_raw') }}
where report_date >= CURRENT_DATE()
