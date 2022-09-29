from dagster import Output, asset, AssetIn
import pandas as pd
from datetime import date
from typing import List

resorts = {
    "ids": ["303001", "303009", "303007","303011"],
    "keys": ["abay", "copper", "breck", "eldora"]
}
asset_keys = resorts["keys"]

def asset_factory(asset_keys: List[str], resorts: dict):
    assets = []
    for i, key in enumerate(asset_keys):

        @asset(
            required_resource_keys={"snocountry_api"},
            name=key,
            io_manager_key="gcs_io_manager",
        )
        def my_asset(context) -> pd.DataFrame:
            api = context.resources.snocountry_api
            report = api.get_resort(resorts["ids"][i])
            return pd.DataFrame(report)

        assets.append(my_asset)
    
    return assets

resort_assets = asset_factory(asset_keys, resorts)


@asset(
    io_manager_key="bq_io_manager",
    required_resource_keys={"bq_auth"},
    ins = {key: AssetIn() for key in asset_keys}
)
def resort_summary(context, **resort_assets) -> pd.DataFrame:
    """Insert clean resort records to BQ"""
    resorts = list(resort_assets.keys())
    resort = resort_assets[resorts[0]]

    resort_summary = pd.DataFrame({
        "resort_name": resort['resortName'],
        "report_date": date.today(),
        "condition": resort['weatherToday_Condition'],	
        "condition_tomorrow": resort['weatherTomorrow_Condition'],		
        "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
        "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
        "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
        "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High'])	
    })

    for resort_name in resorts[1:]:
        resort = resort_assets[resort_name]
        add_to_summary = pd.DataFrame({
            "resort_name": resort['resortName'],
            "report_date": date.today(),
            "condition": resort['weatherToday_Condition'],	
            "condition_tomorrow": resort['weatherTomorrow_Condition'],		
            "low_today": pd.to_numeric(resort['weatherToday_Temperature_Low']),		
            "low_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_Low']),		
            "high_today":	pd.to_numeric(resort['weatherToday_Temperature_High']),	
            "high_tomorrow": pd.to_numeric(resort['weatherTomorrow_Temperature_High'])	
        })
        resort_summary = resort_summary.append(add_to_summary)
    
    return resort_summary


