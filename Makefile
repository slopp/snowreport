build:
	gcloud builds submit --region=us-central1 --tag us-central1-docker.pkg.dev/myhybrid-200215/dagit/snowreport 

k8s_secrets:
	./.bashrc; \
	gcloud container clusters get-credentials autopilot-cluster-1 --region us-central1 --project myhybrid-200215; \
	kubectl delete secret sa-private-key --namespace dagster; \
	kubectl delete secret sa-private-key-id --namespace dagster; \
	kubectl create secret generic sa-private-key \
    	--from-file=SA_PRIVATE_KEY=./private_key \
    	--namespace dagster; \
	kubectl create secret generic sa-private-key-id \
    	--from-literal=SA_PRIVATE_KEY_ID=$$SA_PRIVATE_KEY_ID \
    	--namespace dagster; \


# see https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
k8s_iam_for_gcs:
	gcloud iam service-accounts add-iam-policy-binding 811245043115-compute@developer.gserviceaccount.com \
		--role roles/iam.workloadIdentityUser \
		--member "serviceAccount:myhybrid-200215.svc.id.goog[dagster/user-cloud-dagster-cloud-agent]"; \
	kubectl annotate serviceaccount user-cloud-dagster-cloud-agent \
		--namespace dagster \
		iam.gke.io/gcp-service-account=811245043115-compute@developer.gserviceaccount.com; \
		

helm_repo:
	helm repo add dagster-cloud https://dagster-io.github.io/helm-user-cloud; \
	helm repo update

helm_values: helm_repo
	helm show values dagster-cloud/dagster-cloud-agent

helm_dagster_agent_bd: helm_repo
	gcloud container clusters get-credentials autopilot-cluster-1 --region us-central1 --project myhybrid-200215; \
	helm upgrade \
   		--install user-cloud dagster-cloud/dagster-cloud-agent \
   		--namespace dagster \
   		--set dagsterCloud.deployment=prod \
		--set dagsterCloud.branchDeployments=true \
		--set workspace.serverTTL.enabled=true \
		--set workspace.serverTTL.ttlSeconds=7200; \


#kubectl exec --stdin --tty snowreport-prod-e58f34-7fc5fdc74b-wplxr --namespace dagster -- /bin/bash
#kubectl get pod snowreport-prod-e58f34-7fc5fdc74b-wplxr -o yaml