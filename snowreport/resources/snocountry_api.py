import pandas as pd
import requests
from dagster import resource


SNOCOUNTRY_BASE_URL = 'http://feeds.snocountry.net/conditions.php?apiKey=SnoCountry.example&ids='

class SnocountryAPI():
    def get_resort(self, resort_id: int):
        url = f"{SNOCOUNTRY_BASE_URL}{resort_id}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Something failed requesting: "+request_url)
            report = {}
        else:
            report = response.json()['items']
        return report


@resource(description="Returns resort reports from snocountry's conditions API")
def snocountry_api_client(_):
    return SnocountryAPI()