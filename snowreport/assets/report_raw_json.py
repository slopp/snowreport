from dagster import Output, asset, AssetIn
import pandas as pd

@asset(
    required_resource_keys={"snocountry_api"},
    key_prefix=["raw"],
    #io_manager_key="gcs_io_manager",
)
def resort(context) -> pd.DataFrame:
    """Raw resort report from snocountry conditions API"""
    api = context.resources.snocountry_api
    report = api.get_resort("303001")
    return pd.DataFrame(report)


@asset(
    io_manager_key="bq_io_manager",
    ins={"resort": AssetIn()},
)
def resort_summary(context, resort: pd.DataFrame) -> pd.DataFrame:
    """Insert clean resort records to BQ"""
    resort_summary = pd.DataFrame({
        "resort_name": resort['resortName'],
        "report_date": pd.to_datetime(resort['reportDateTime']),
        "condition": resort['weatherToday_Condition'],	
        "condition_tomorrow": resort['weatherTomorrow_Condition'],		
        "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
        "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
        "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
        "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High'])	
    })
    return resort_summary

