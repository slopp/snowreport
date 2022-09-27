# snowreport

This is an attempt to build out a simple pipeline in dagster that reads data from an API and stores the result in GCS, and then compiles a "clean" version of the result in BQ.

More details to come.

A few key notes:
- the custom bg_io_manager expects the BQ dataset and table to already exist
- you'll need to provide SA JSON for the BQ read/write operations, see the repository resource config
- the GCS operations are done using the scopes / IAM privileges of the underlying compute, not the SA account (for now)

