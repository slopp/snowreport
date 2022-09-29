build:
	gcloud builds submit --region=us-central1 --tag us-central1-docker.pkg.dev/myhybrid-200215/dagit/snowreport 

k8s_secrets:
	./.bashrc; \
	gcloud container clusters get-credentials autopilot-cluster-1 --region us-central1 --project myhybrid-200215; \
	kubectl create secret generic sa-private-key \
    	--from-literal=SA_PRIVATE_KEY=$SA_PRIVATE_KEY \
    	--namespace dagster; \
	kubectl create secret generic sa-private-key-id \
    	--from-literal=SA_PRIVATE_KE_ID=$SA_PRIVATE_KEY_ID \
    	--namespace dagster; \
	
