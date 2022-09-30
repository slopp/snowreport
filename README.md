# snowreport

This is an attempt to build out a simple pipeline in dagster that reads data from an API and stores the result in GCS, and then compiles a "clean" version of the result in BQ.

![dashboard image](./snowreportv3.png)

Report result: https://datastudio.google.com/reporting/136a93b3-8070-410a-a884-f0f657307d12

I've built this same pipeline in [R](https://github.com/slopp/scheduledsnow) and [GCP](https://github.com/slopp/embed-snow). This time is a little different, but kind of the same.

![dagster image](./snowreportdagster.png)

## Project Evolution 

The evolution of this project:

- The R version relied on local storage, and production was scheduled on RStudio Connect and used a "production" volume mounted to the server. One scheduled function pulled all the data. A second scheduled function cleaned the data and generated a report. The two schedules were not connected, just run a half hour apart.   

- The second version of the project used all the GCP services. A scheduled Cloud Function would pull the data for all resorts and write it to GCS. Then a constantly running ($$$) Dataflow job would read the GCS data and write it to BigQuery. Looker did most of the clean up and surfaced the resulting dashboard in a website using an iframe embed.  

- This version uses dagster! A few of the key benefits are:  
    - There is now a separation between the production pipeline, my local testing, and a staging pipeline that runs on PRs to the code. This is the first version of the project tightly coupled with version control.  

    - The different environments use the same logic, but different resources. The local pipeline runs with just pandas dataframes that are stored on disk. The staging pipeline writes the resort data to GCS and then loads and cleans it in BigQuery, within a staging dataset (schema). The production pipeline is the same as the staginging pipeline, but uses the production dataset (schema).  

    - The dagster version of the project correctly reflects the dependency between the resort data and the final summary tables. Each resort data pull is an independent step instead of all the resort data being pulled in one function with a for-loop. This separation makes it easy to re-run one resort if the API call fails. The resort summary can be updated with the new resort data while using cached results for the other resorts.

    - This version uses DataStudio for the report visualization. As you can tell, my interest in the reporting layer has decreased over time while my interest in the backend pipeline has increased. :shrug:. The report probably looks the best in DataStudio anyway which is a testament to how cruddy I am at CSS regardless of the platform or level of interest.

All in all, this version of the project definitely required the most investment, but it also feels the most robust. In refactoring the code I caught mistakes in my staging environment that would have just trashed my other "production" versions of the project.


## Why Dagster

I could have used Airflow, but opted to use Dagster because:

### Dataset Aware

Dagster is aware that my goal is to create datasets. This awareness makes it possible for me to "re-materialize" specific assets (like data from one resort) and to see asset lineage. In comparison, other schedulers just execute tasks and lack the rich metadata and handy interface that is aware of the results.  

![dagster assets](./dagsterassetviz.png)

### Code Structure and Local Development

Because Dagster knows that I'm building datasets, it has strong opinions about how to structure my code. The data processing logic is separate from the data storage logic. This separation made it easy for me to have local development build on pandas with staging and production built on GCS and BigQuery. The core logic was the same, see `assets`, and the different storage for local/staging/prod was handled by `resources`. While you can fuss around with `if` statements to achieve similar outcomes in other tools, the first class support in Dagster makes a world of difference.

Speaking of local development, in dagster I developed everything locally with Python. I didn't have to mess with Docker or minikube. In other schedulers I would have done the initial development with cloud resources, which dramatically slows things down (see v2 of this project). I get really distracted if I have to wait for Kubernetes schedulers to test a code change!

 Once my dagster code was ready I did have to setup my production deployment, which took some Kubernetes iterations. However, those iterations were config iterations not code changes - a one-time setup cost for the project. Now that production and staging are configured, I can make changes to my core code locally without ever waiting on the Kubernetes setup.

### Internal Architecture

Airflow workers load all the code all the time. This architecture can create performance issues, but it also causes a dependency nightmare where the data transformation python code has to be compatible with airflow's internal dependencies. The natural workaround to these two problems is to create distinct Airflow clusters for everything, which sort of defeats the point of a scheduler knowing about the dependencies between things!

Dagster's built differently and ensures that the Dagster control plane is separate from my user code. For a toy project like this one the impact is mostly hypothetical, but for actual workloads these architecture hurdles a big deal.

## About the Environment

This project is using Dagster Cloud's Hybrid deployment model. Basically:  

1. I wrote my code and ran it locally using just a Python virtual environment. I was also able to test my staging and production resources (GCS and BigQuery) using my local environment by supplying the right GCP IAM permissions to the environment.  

2. Next I setup Dagster Cloud which serves as my control plane. I also setup a GKE autopilot cluster which would serve as my execution plane.  

3. Once my code was ready to be deployed, I made a few modifications to prepare it for primetime. I added a Dockerfile and dagster deployment configs. I also setup a Google Artifact Registry to house the Docker images containing my code. The code itself runs in GKE while Dagster Cloud keeps track of everything.  


A few things that I did here are worth calling out for future me:

- I wrote a custom `bq_io_manager` to handle writing my results to BQ, and my implementation the BQ dataset and table to already exist and be supplied as resource configuration.  

- I decided to make life a little hard for myself to test out a few different ways to handle authenticating to external services. For the GCS writing, I rely on the underlying environment to havthee access. In production, this is done by having the Kubernetes service account access a GCP IAM service account in a convulted process called workload identity. See the makefile `k8s_iam_for_gcs` for details. For BQ, I went with the explicit approach of having the credentials supplied to the client code. Locally those credentials are passed through environment variables. In production those environment variables are set through K8s secrets, see the make target `k8s_secrets`. The v1 R version of this project had a lot less permissioning headaches.

- My repo is setup to build my dagster code into a Docker image for each commit to a PR. This is great for testing changes, but if I just want to update this ReadMe I can have GH skip those actions by including `[skip ci]` in the commit message.

- My development environment for this work was VS Code + a GCP VM. Most of the helpful commands live in the `Makefile`, but:

```
# to get VS Code to talk to the VM
gcloud compute config-ssh
```

## Future Work

- [ ] Figure out how to use Dagster partitions.
- [ ] Once the ski season begins, update the code to show snowfall totals, predictions, and trail status. 
- [ ] Add a resort facts table.
- [ ] Cost

## Getting Started

After cloning this repo run `pip install .[dev]`. Then run `dagit`. Everything will run in `local` mode which doesn't require any resources or secrets!

To get going with GCS and BQ, modify the `repository.py` resource config as appropriate and ensure you have a `SA_PRIVATE_KEY` and `SA_PRIVATE_KEY_ID` set. `SA` is short for GCP service account. The IAM permissions required for that service account are...well...least privilege would suggest they should be few and far between. I just gave my SA Cloud Storage Admin and BigQuery Admin roles.


