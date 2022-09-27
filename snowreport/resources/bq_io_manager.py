import pandas as pd
from dagster import IOManager, io_manager
from dagster import _check as check
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas_gbq


class BQIOManager(IOManager):
    """Inserts data into existing BQ table."""

    def handle_output(self, context, obj):
        if not isinstance(obj, pd.DataFrame):
            check.failed(f"Outputs of type {type(obj)} not supported.")

        project_id = context.resource_config["project_id"]
        sa_json = context.resource_config["sa_json"]
        table_id = context.resource_config["table_id"]

        credentials = service_account.Credentials.from_service_account_info(sa_json)
        client = bigquery.Client(credentials=credentials, project=project_id)

        job_config = bigquery.LoadJobConfig(      
            autodetect=False,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        )

        job = client.load_table_from_dataframe(
            obj, table_id, job_config
        )  
        job.result()
        

    def load_input(self, context):
        project_id = context.resource_config["project_id"]
        sa_json = context.resource_config["sa_json"]
        table_id = context.resource_config["table_id"]

        if context.dagster_type.typing_type == pd.DataFrame:
            credentials = service_account.Credentials.from_service_account_info(sa_json)
            sql = f"SELECT * FROM {table_id}"
            df = pandas_gbq.read_gbq(sql, project_id=project_id, credentials=credentials)
        
            return df

        check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input either on the argument of the @asset-decorated function."
        )

@io_manager(config_schema={"table_id": str, "sa_json": dict, "project_id": str})        
def bq_io_manager(init_context):
    return BQIOManager()