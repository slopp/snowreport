from dagster import load_assets_from_package_module, repository, with_resources
from dagster_gcp.gcs import gcs_pickle_io_manager
from dagster_gcp.gcs import gcs_resource
from snowreport import assets
from snowreport.resources import snocountry_api_client, bq_io_manager, bq_auth, bq_writer
from snowreport.jobs import resort_clean
import os

sa_json = {
    "production": 
        {
            "type": "service_account",
            "project_id": "myhybrid-20021",
            "client_email": "811245043115-compute@developer.gserviceaccount.com",
            "client_id": "105707464203810563700",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/811245043115-compute%40developer.gserviceaccount.com"
        }
}

# todo...make this DRY
resource_defs = {
    "production": 
        {
                "snocountry_api": snocountry_api_client,
                "gcs_io_manager": gcs_pickle_io_manager.configured({
                    "gcs_bucket": "lopp_snow_report_raw"
                }),
                "gcs": gcs_resource.configured({
                    "project": "myhybrid-200215"
                }),
                "bq_auth": bq_auth.configured({
                    "sa_private_key_id":  {"env": "SA_PRIVATE_KEY_ID"},
                    "sa_private_key": {"env": "SA_PRIVATE_KEY"},
                }),
                "bq_writer": bq_writer.configured({
                    "sa_json": sa_json["production"],
                    "project_id": "myhybrid-200215",
                    "dataset": "snowreport"
                }), 
                "bq_io_manager": bq_io_manager.configured({
                    "sa_json": sa_json["production"],
                    "table_id": "myhybrid-200215.snowreport.resort_raw",
                    "project_id": "myhybrid-200215"
                })
        }
}

DEPLOYMENT = os.getenv("DAGSTER_DEPLOYMENT", "production")

all_assets = load_assets_from_package_module(assets)

all_jobs = [resort_clean.to_job(resource_defs=resource_defs[DEPLOYMENT])]

@repository
def snowreport():
    definitions = [
        with_resources(all_assets,resource_defs[DEPLOYMENT]), 
        all_jobs
    ]
    return definitions
