# snowreport

This is an attempt to build out a simple pipeline in dagster that reads data from an API and stores the result in GCS, and then compiles a "clean" version of the result in BQ.

I've built this same pipeline in [R](https://github.com/slopp/scheduledsnow) and [GCP](https://github.com/slopp/embed-snow), but dagster adds:

- the ability to re-run only certain assets (eg specific resorts)
- the ability to see the dependencies between assets 

More details to come.

A few key notes:
- My custom bq_io_manager expects the BQ dataset and table to already exist
- You'll need to provide GCP SA JSON for the BQ read/write operations, see the repository resource config. Right now the secret key and id are made available through environment variables, and in production those environment variables are supplied as k8s secrets, see the make target `k8s_secrets`.
- The GCS operations are done using the scopes / IAM privileges of the underlying compute, not the SA account. In GKE autopilot clusters this is rather confusing, see the makefile target `k8s_iam_for_gcs` which ties the SA in K8s to the IAM SA allowing GCS writes to work.

Areas of improvement:
- consider using partitions?
- figure out a way to make the definition of assets more DRY... potentially through an asset factory

```
def asset_factory(asset_keys: List[str]):
    assets = []
    for key in asset_keys:

        @asset(name=key)
        def my_asset():
            same_logic(key)

        assets.append(my_asset)
    
    return assets
```

Next up, try to get this running in Dagster Cloud with GKE and branch deployments.

## To get started

After cloning this repo you can run `pip install .[dev]`. 

Then modify the repository.py resource config as appropriate.

Ensure you have `SA_PRIVATE_KEY` and `SA_PRIVATE_KEY_ID` set.

Then run `dagit`. 

