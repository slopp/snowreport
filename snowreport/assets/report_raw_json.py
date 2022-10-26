from dagster import Output, asset, AssetIn, DailyPartitionsDefinition
import pandas as pd
from datetime import date
from typing import List

resorts = {
    "ids": ["303001", "303009", "303007","303011"],
    "keys": ["abay", "copper", "breck", "eldora"]
}
asset_keys = resorts["keys"]

def get_resort_id_from_name(resort_name: str):
    idx = resorts["keys"].index(resort_name)
    return resorts["ids"][idx]

def asset_factory(asset_keys: List[str], resorts: dict):
    assets = []
    for i, key in enumerate(asset_keys):

        @asset(
            required_resource_keys={"snocountry_api"},
            name=key,
            io_manager_key="gcs_io_manager",
            partitions_def=DailyPartitionsDefinition(start_date="2022-10-05")
        )
        def my_asset(context) -> pd.DataFrame:
            api = context.resources.snocountry_api
            resort_id = get_resort_id_from_name(context.op_def.name)
            report = api.get_resort(resort_id)
            return pd.DataFrame(report)

        assets.append(my_asset)
    
    return assets

resort_assets = asset_factory(asset_keys, resorts)


@asset(
    io_manager_key="bq_io_manager",
    required_resource_keys={"bq_auth"},
    ins = {key: AssetIn(key) for key in asset_keys},
    partitions_def=DailyPartitionsDefinition(start_date="2022-10-05"),
    key_prefix="snocountry"
)
def resort_raw(context, **resort_assets) -> pd.DataFrame:
    """Insert clean resort records to BQ"""
    resorts = list(resort_assets.keys())
    resort = resort_assets[resorts[0]]
    resort_summary = pd.DataFrame({
        "resort_name": resort['resortName'],
        "report_date": pd.to_datetime(context.asset_partition_key_for_output()),
        "condition": resort['weatherToday_Condition'],	
        "condition_tomorrow": resort['weatherTomorrow_Condition'],		
        "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
        "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
        "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
        "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High']),
        "open_trails": 	pd.to_numeric(resort['openDownHillTrails'])
    })

    for resort_name in resorts[1:]:
        
        resort = resort_assets[resort_name] 
        
        add_to_summary = pd.DataFrame({
            "resort_name": resort['resortName'],
            "report_date": pd.to_datetime(context.asset_partition_key_for_output()),
            "condition": resort['weatherToday_Condition'],	
            "condition_tomorrow": resort['weatherTomorrow_Condition'],		
            "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
            "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
            "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
            "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High']),
            "open_trails": 	pd.to_numeric(resort['openDownHillTrails'])	
        })
        resort_summary = resort_summary.append(add_to_summary)
    
    return resort_summary


