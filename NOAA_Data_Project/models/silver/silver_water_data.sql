select
    t as observed_at,
    v as water_level_ft,
    pulled_at
from {{ source('noaa', 'bronze_water_data') }}
where v is not null

--source instead of ref because this is a source table, not a model.
--Ref is used for models that are built from other models or sources within duckdb. 
--In this case, we are directly querying the source table 'bronze_water_data' from the 'noaa' source, 
--so we use the source function to reference it.