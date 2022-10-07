from tracemalloc import start
from dagster import DailyPartitionsDefinition, build_schedule_from_partitioned_job, repository, with_resources, fs_io_manager
from dagster import AssetSelection, define_asset_job, ScheduleDefinition 
from dagster import AssetKey, EventLogEntry, SensorEvaluationContext, asset_sensor, RunRequest
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from dagster_gcp.gcs import gcs_pickle_io_manager
from dagster_gcp.gcs import gcs_resource
from snowreport.assets import resort_raw, resort_assets
from snowreport.resources import snocountry_api_client, bq_io_manager, bq_auth, bq_writer, bq_auth_fake
from snowreport.jobs import resort_clean
import os
from dagster._utils import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../snowdb")
DBT_PROFILES_DIR = file_relative_path(__file__, "../snowdb/config")

###################
# Resources
###################

def get_current_env():
    is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
    assert is_branch_depl != None  # env var must be set
    return "branch" if is_branch_depl else os.getenv("DAGSTER_DEPLOYMENT", "local")

DEPLOYMENT = get_current_env()

sa_json = {
    "type": "service_account",
    "project_id": "myhybrid-20021",
    "client_email": "811245043115-compute@developer.gserviceaccount.com",
    "client_id": "105707464203810563700",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/811245043115-compute%40developer.gserviceaccount.com"
}

# TODO...make this DRY
# bq_io_manager - requires a table to already exists and appends records to it
# bq_auth - used by bq_writer eand bq_io_manager
# bq_writer - is for the resort clean job, runs a CREATE TABLE statement directly 
# gcs_io_manager + gcs - used to write raw API results to GCS as pickled objects
# snocountry_api - uses a developer test key to access snocountry API
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
                    "sa_json": sa_json,
                    "project_id": "myhybrid-200215",
                    "dataset": "snowreport"
                }), 
                "bq_io_manager": bq_io_manager.configured({
                    "sa_json": sa_json,
                    "table_id": "myhybrid-200215.snowreport.resort_raw",
                    "project_id": "myhybrid-200215"
                }),
                "dbt": dbt_cli_resource.configured({ "project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR,  "target": "prod" })
        },
    "local": 
        # fake it till you make it
        {
                "snocountry_api": snocountry_api_client,
                #"gcs_io_manager": fs_io_manager.configured({"base_dir": os.environ["DAGSTER_HOME"]+"/storage"}),
                "gcs_io_manager": fs_io_manager,
                "gcs": gcs_resource.configured({"project": "fake"}),
                "bq_auth": bq_auth_fake,
                "bq_io_manager": fs_io_manager,
                # TODO remove this if clean job and sensor can be eliminated from local repo
                "bq_writer": bq_auth_fake,
                # TODO figure out how to have dbt use a local duckdb not BQ, will require a diff mock bq_io_manager beyond fs_io_manager
                "dbt": dbt_cli_resource.configured({ "project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR,  "target": "branch" })
        },
    "branch": 
        {
                "snocountry_api": snocountry_api_client,
                "gcs_io_manager": gcs_pickle_io_manager.configured({
                    "gcs_bucket": "lopp_snow_report_branch_raw"
                }),
                "gcs": gcs_resource.configured({
                    "project": "myhybrid-200215"
                }),
                "bq_auth": bq_auth.configured({
                    "sa_private_key_id":  {"env": "SA_PRIVATE_KEY_ID"},
                    "sa_private_key": {"env": "SA_PRIVATE_KEY"},
                }),
                "bq_writer": bq_writer.configured({
                    "sa_json": sa_json,
                    "project_id": "myhybrid-200215",
                    "dataset": "snowreport_branch"
                }), 
                "bq_io_manager": bq_io_manager.configured({
                    "sa_json": sa_json,
                    "table_id": "myhybrid-200215.snowreport_branch.resort_raw",
                    "project_id": "myhybrid-200215"
                }),
                "dbt": dbt_cli_resource.configured({ "project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR, "target": "branch"})
        },
    
}

###################
# Assets & Jobs
###################

dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    io_manager_key="bq_io_manager"
)

all_assets = [*resort_assets, resort_raw, *dbt_assets]
asset_job = define_asset_job(
    "asset_job",
     AssetSelection.groups("default"),
     partitions_def=DailyPartitionsDefinition(start_date="2022-10-05")
)
resort_clean_job = resort_clean.to_job(resource_defs=resource_defs[DEPLOYMENT])


###################
# Schedules & Sensors
###################

daily_schedule = build_schedule_from_partitioned_job(asset_job)

@asset_sensor(asset_key=AssetKey(["snocountry", "resort_raw"]), job=resort_clean_job)
def my_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(
        run_key=context.cursor
    )


###################
# Repository
###################

@repository
def snowreport():
    definitions = [
        with_resources(all_assets,resource_defs[DEPLOYMENT]), 
        [resort_clean_job, asset_job],
        [daily_schedule],
        [my_asset_sensor]
    ]
    return definitions
