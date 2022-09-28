
from dagster import op, graph

@op(required_resource_keys={"bq_auth", "bq_writer"})
def write_unique_rows(context):
    context.resources.bq_writer.execute_query(
        "CREATE OR REPLACE TABLE `resort_clean` AS (SELECT DISTINCT * FROM `resort_raw`)"
    )

@graph
def resort_clean():
    write_unique_rows()
