# snowreport

This is an attempt to build out a simple pipeline in dagster that reads data from an API and stores the result in GCS, and then compiles a "clean" version of the result in BQ.

I've built this same pipeline in [R](https://github.com/slopp/scheduledsnow) and [GCP](https://github.com/slopp/embed-snow), but dagster adds:

- the ability to re-run only certain assets (eg specific resorts)
- the ability to see the dependencies between assets 

More details to come.

A few key notes:
- My custom bg_io_manager expects the BQ dataset and table to already exist
- You'll need to provide GCP SA JSON for the BQ read/write operations, see the repository resource config. Right now the secret key and id are passed as a separate config which can be entered at runtime in the dagit launchpad to avoid commiting those into Git
- The GCS operations are done using the scopes / IAM privileges of the underlying compute, not the SA account

Areas of improvement:
- include the date in the report asset key, or even consider using partitions
- figure out a way to make the definition of assets more DRY

## To get started

After cloning this repo you can run `pip install .[dev]`. 

Then modify the repository.py resource config as appropriate.

Then run `dagit`. 

