from unicodedata import numeric
from numpy import float64, int64, datetime64
from snowreport.assets.report_raw_json import resort_summary
from dagster import fs_io_manager, with_resources, build_op_context
from snowreport.resources import  bq_auth_fake
import pandas as pd
import pytest

resort = {
    "resortName": ["test"],
    'weatherToday_Condition': ["Snow"],
    'weatherTomorrow_Condition': ["Sunny"],
    'weatherToday_Temperature_Low': ["30"],
    'weatherTomorrow_Temperature_Low': ["16"],
    'weatherToday_Temperature_High': ["48"],
    'weatherTomorrow_Temperature_High': ["37"]
}

resorts = {
    "abay":resort,
    "copper":resort
}

RESULT_SCHEMA = {
    "resort_name": str,
    "report_date": datetime64,
    "condition": str,
    "condition_tomorrow": str,
    "low_today": float64,
    "low_today": int64,
    "low_tomorrow": int64,
    "high_today":	int64,
    "high_tomorrow": int64
}

@pytest.mark.parametrize(
    "resorts, RESULT_SCHEMA",
    [(resorts, RESULT_SCHEMA)]
)
def test_schema_final_results(resorts, RESULT_SCHEMA):
    resort_summary_with_resources = with_resources(
        [resort_summary], {"bq_auth": bq_auth_fake, "bq_io_manager": fs_io_manager}
    )[0]
    result = resort_summary_with_resources(build_op_context(), **resorts)

    assert type(result) == pd.DataFrame
    assert len(result) == 2
    for column in result.columns:
        assert type(result[column].values[0]) == RESULT_SCHEMA[column]
    




