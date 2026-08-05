with tide as (
    select
        *,
        avg(water_level_ft) OVER (
            ORDER BY observed_at ROWS BETWEEN 30 PRECEDING AND 30 FOLLOWING
        ) as smoothed_level
    from "NOAA_Data"."main"."silver_water_data"
),
tide_trend as (
    select
        *,
        smoothed_level - lag(smoothed_level, 30) over (order by observed_at) as tide_slope
    from tide
),
wind as (
    select * from "NOAA_Data"."main"."silver_wind_data"
)

select
    t.observed_at,
    t.water_level_ft,
    w.wind_speed_kts,
    case
        when w.wind_speed_kts is null then null
        when w.wind_speed_kts < 5 then 'calm'
        when w.wind_speed_kts < 12 then 'breezy'
        else 'windy'
    end as wind_category,
    case 
        when t.tide_slope is null then null
        when t.tide_slope < -0.15 then 'falling'
        when t.tide_slope > 0.15 then 'rising'
        else 'steady'
    end as tide_direction
from tide_trend t
left join wind w on t.observed_at = w.observed_at