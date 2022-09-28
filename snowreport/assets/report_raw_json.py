from dagster import Output, asset, AssetIn
import pandas as pd
from datetime import date

today = str(date.today())

@asset(
    required_resource_keys={"snocountry_api"},
    key_prefix=["raw", today],
    io_manager_key="gcs_io_manager",
)
def abay(context) -> pd.DataFrame:
    """Raw resort report from snocountry conditions API"""
    api = context.resources.snocountry_api
    report = api.get_resort("303001")
    return pd.DataFrame(report)

@asset(
    required_resource_keys={"snocountry_api"},
    key_prefix=["raw", today],
    io_manager_key="gcs_io_manager",
)
def copper(context) -> pd.DataFrame:
    """Raw resort report from snocountry conditions API"""
    api = context.resources.snocountry_api
    report = api.get_resort("303009")
    return pd.DataFrame(report)

@asset(
    required_resource_keys={"snocountry_api"},
    key_prefix=["raw", today],
    io_manager_key="gcs_io_manager",
)
def breck(context) -> pd.DataFrame:
    """Raw resort report from snocountry conditions API"""
    api = context.resources.snocountry_api
    report = api.get_resort("303007")
    return pd.DataFrame(report)

@asset(
    required_resource_keys={"snocountry_api"},
    key_prefix=["raw", today],
    io_manager_key="gcs_io_manager",
)
def eldora(context) -> pd.DataFrame:
    """Raw resort report from snocountry conditions API"""
    api = context.resources.snocountry_api
    report = api.get_resort("303011")
    return pd.DataFrame(report)    


@asset(
    io_manager_key="bq_io_manager",
    required_resource_keys={"bq_auth"},
    ins={"abay": AssetIn(), "breck": AssetIn(), "copper": AssetIn(), "eldora": AssetIn()},
)
def resort_summary(context, abay: pd.DataFrame, breck: pd.DataFrame, copper: pd.DataFrame, eldora: pd.DataFrame) -> pd.DataFrame:
    """Insert clean resort records to BQ"""
    resort = abay

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

    for resort in [breck, copper, eldora]:
        add_to_summary = pd.DataFrame({
            "resort_name": resort['resortName'],
            "report_date": pd.to_datetime(resort['reportDateTime']),
            "condition": resort['weatherToday_Condition'],	
            "condition_tomorrow": resort['weatherTomorrow_Condition'],		
            "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
            "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
            "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
            "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High'])	
        })
        resort_summary = resort_summary.append(add_to_summary)
    
    return resort_summary


