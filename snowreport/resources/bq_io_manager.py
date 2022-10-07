import pandas as pd
from dagster import IOManager, io_manager, resource, StringSource
from dagster import _check as check
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas_gbq

class BQIOManager(IOManager):
    """Inserts data into existing BQ table."""

    def __init__(self, sa_private_key_id, sa_private_key):
        self.sa_private_key_id = sa_private_key_id
        self.sa_private_key = sa_private_key.replace(r'\n', '\n') 

    def handle_output(self, context, obj):
        if not isinstance(obj, pd.DataFrame):
            check.failed(f"Outputs of type {type(obj)} not supported.")

        project_id = context.resource_config["project_id"]
        sa_json = {"private_key": self.sa_private_key, "private_key_id": self.sa_private_key_id}
        sa_json.update(context.resource_config["sa_json"])
        table_id = context.resource_config["table_id"]
        
    
        credentials = service_account.Credentials.from_service_account_info(sa_json)
        client = bigquery.Client(credentials=credentials, project=project_id)

        job_config = bigquery.LoadJobConfig(      
            autodetect=False,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        )
        # defaults to appending records, so this takes the current asset pandas df 
        # and adds it to the existing table
        job = client.load_table_from_dataframe(
            obj, table_id, job_config
        )  
        job.result()
        

    def load_input(self, context):
        project_id = context.resource_config["project_id"]
        sa_json = {"private_key":self.sa_private_key, "private_key_id": self.sa_private_key_id}
        sa_json.update(context.resource_config["sa_json"])
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

@io_manager(config_schema=
    {
        "table_id": str, 
        "sa_json": dict, 
        "project_id": str,
    },
    required_resource_keys={"bq_auth"}
)        
def bq_io_manager(init_context):
    id, key = init_context.resources.bq_auth
    return BQIOManager(id,  key)

@resource(config_schema = {"sa_private_key": StringSource, "sa_private_key_id": StringSource})
def bq_auth(context):
    return(context.resource_config["sa_private_key_id"],context.resource_config["sa_private_key"] )


@resource(config_schema=
    {
        "dataset": str, 
        "sa_json": dict, 
        "project_id": str,
    },
    required_resource_keys={"bq_auth"}
) 
def bq_writer(init_context):
    id, key = init_context.resources.bq_auth
    return BQWriter(id,  key, init_context)

class BQWriter():
    def __init__(self, sa_private_key_id, sa_private_key, context):
        self.sa_private_key_id = sa_private_key_id
        self.sa_private_key = sa_private_key.replace(r'\n', '\n')
        self.context = context

    def execute_query(self, query):
        project_id = self.context.resource_config["project_id"]
        sa_json = {"private_key":self.sa_private_key, "private_key_id": self.sa_private_key_id}
        sa_json.update(self.context.resource_config["sa_json"])
        dataset = self.context.resource_config["dataset"]

        credentials = service_account.Credentials.from_service_account_info(sa_json)
        client = bigquery.Client(credentials=credentials, project=project_id)

        job_config = bigquery.QueryJobConfig()
        job_config.default_dataset = project_id+"."+dataset
        
        
        query_job = client.query(query,job_config) 
        query_job.result()  