# snowreport

This is an attempt to build out a simple pipeline in dagster that reads data from an API and stores the result in GCS, and then compiles a "clean" version of the result in BQ.

![dashboard image](./snowreportv3.png)

Report result: https://datastudio.google.com/reporting/136a93b3-8070-410a-a884-f0f657307d12

I've built this same pipeline in [R](https://github.com/slopp/scheduledsnow) and [GCP](https://github.com/slopp/embed-snow), but this time is a little different, but kind of the same.

![dagster image](./snowreportdagster.png)

## Project Evolution 

The evolution of this project:

- The R version relied on local storage, and production was scheduled on RStudio Connect and used a "production" volume mounted to the server. One scheduled function pulled all the data. A second scheduled function cleaned the data and generated a report. The two schedules were not connected, just run a half hour apart.   

- The second version of the project used all the GCP services. A scheduled cloud function would pull the data for all resorts and write it to GCS. Then a constantly running ($$$) Dataflow job would read the GCS data and write it to BigQuery. Looker did most of the clean up and surfaced the resulting dashboard in a website using an iframe embed.  

- This version uses dagster! A few of the key benefits are:  
    - There is now a separation between the production pipeline, my local testing, and a staging pipeline that runs on PRs to the code. This is the first version of the project tightly coupled with version control.  

    - The different environments use the same logic, but different resources. The local pipeline runs with just pandas dataframes that are stored on disk. The staging pipeline writes the resort data to GCS and then loads and cleans it in BigQuery, within a staging dataset (schema). The production pipeline is the same as the staginging pipeline, but uses the production dataset (schema).  

    - The dagster version of the project correctly reflects the dependencies between the resorts and the final summary tables. Additionally, the data pulls from each resort are independent instead of being one function with a for-loop. This separation makes it easy to re-run one resort if the API call fails while still updating the resort summary with cached results for the other resorts.

    - This version uses DataStudio for the report visualization. As you can tell, my interest in the reporting layer has decreased over time while my interest in the backend pipeline has increased. :shrug:. The report probably looks the best in DataStudio which is a testament to how cruddy I am at CSS regardless of the platform or level of interest.

All in all, this version of the project definitely required the most investment, but it also feels the most robust. In refactoring the code I caught mistakes in my staging environment that would have just trashed my other "production" versions of the project.


## Why Dagster

I could have used Airflow, but opted to use Dagster because:

### Dataset Aware

Dagster is aware that my goal is to create datasets. This awareness makes it possible for me to "re-materialize" specific assets (like data from one resort) and to see asset lineage. In comparison, other schedulers just execute tasks and lack the rich metadata and handy interface that is aware of the results.  

### Code Structure

Another benefit of Dagster knowing that data is my aim is dagster has strong opinions about how to separate the data processing logic from the data storage logic. This separation enables the different behavior in local/staging/production environments. Sure in other schedulers you can fuss about with if statements to change schemas, but if you want totally seperate resources for local testing than at some point your if statement becomes:

```
if local:
    localOp
else:
    productionOp
```

In dagster, the logical code is the same even if my local environment is using pandas and pickle files and production is using BigQuery. 

I also really liked that in dagster I could run everything locally with just Python before swallowing Docker and Kubernetes setup.

### Performance

Airflow workers load all the code all the time. This can create performance issues, but it also causes a dependency nightmare where all python code has to be compatible airflow package versions. The natural workaround is to create separate Airflow clusters for everything, which sort of defeats the point of a scheduler knowing about dependencies between things!

Dagster works differently and ensures that dagster's scheduler is separate from my user code which means we can have different dependencies and avoid performance concerns.

## About the Environment

This project is using Dagster Cloud's Hybrid deployment model. Basically:  

1. I wrote my code and ran it locally using just a Python virtual environment. I was also able to test my staging and production resources (GCS and BigQuery) using my local environment by supplying the right GCP IAM permissions to the environment.  

2. Next I setup Dagster Cloud which serves as my control plane. I also setup a GKE autopilot cluster which would serve as my execution plane.  

3. Once my code was ready to be deployed, I made a few modifications to prepare it for primetime. I added a Dockerfile and dagster deployment configs. I also setup a Google Artifact Registry to house the Docker images containing my code. The code itself runs in GKE while Dagster Cloud keeps track of everything.  


A few things that I did here are worth calling out for future me:

- I wrote a custom `bq_io_manager` to handle writing my results to BQ, and my implementation the BQ dataset and table to already exist and be supplied as resource configuration.  

- I decided to make life a little hard for myself to test out a few different ways to handle authenticating to external services. For the GCS writing, I rely on the underlying environment to havthee access. In production, this is done by having the Kubernetes service account access a GCP IAM service account in a convulted process called workload identity. See the makefile `k8s_iam_for_gcs` for details. For BQ, I went with the explicit approach of having the credentials supplied to the client code. Locally those credentials are passed through environment variables. In production those environment variables are set through K8s secrets, see the make target `k8s_secrets`. The v1 R version of this project had a lot less permissioning headaches.

- My repo is setup to build my dagster code into a Docker image for each commit to a PR. This is great for testing changes, but if I just want to update this ReadMe I can have GH skip those actions by including `[skip ci]` in the commit message.

- My development environment for this work was VS Code + a GCP VM. A few helpful commands:

```
# to get VS Code to talk to the VM
gcloud compute config-ssh
```

## Future Work

- [ ] Figure out how to use dagster partitions.
- [ ] Once the ski season begins, update the code to show snowfall totals, predictions, and trail status. 
- [ ] Add a resort facts table.
- [ ] Cost

## Getting Started

After cloning this repo run `pip install .[dev]`. Then run `dagit`. Everything will run in `local` mode which doesn't require any resources or secrets!

To get going with GCS and BQ, modify the `repository.py` resource config as appropriate and ensure you have a `SA_PRIVATE_KEY` and `SA_PRIVATE_KEY_ID` set. `SA` is short for GCP service account. The IAM permissions required for that service account are...well...least privilege would suggest they should be few and far between. I just gave my SA Cloud Storage Admin and BigQuery Admin roles.


