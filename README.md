# Reader and Writer ecosystem

## Usage
In order to setup required environment please run init.sh script with root privileges. Debian based OS is supported. Script is tested in Ubuntu 18.04 environment.
Once all dependencies are set and script successfully terminated, you should get:
- reader and writer deployments in the app namespace together with mysql sts (master+slave)
```console
kubectl get pods -n app
NAME                      READY   STATUS    RESTARTS   AGE
mysql-primary-0           1/1     Running   0          3h56m
mysql-secondary-0         1/1     Running   0          3h56m
reader-b9ccb949d-65thf    1/1     Running   0          3h53m
reader-b9ccb949d-72bdz    1/1     Running   0          3h53m
reader-b9ccb949d-thqp5    1/1     Running   0          3h53m
writer-5c4fbd9dc4-9vx78   1/1     Running   0          3h53m
```
- Prometheus and grafana deployments deployed to default namespace
```console
kubectl get pods
NAME                                 READY   STATUS    RESTARTS   AGE
grafana-6bb6bbf7dd-n7gtq             1/1     Running   0          18m
prometheus-server-54c94bf7d6-t47p5   2/2     Running   0          3h55m
```
In order to connect to grafana, you must run port-forwarding on minukube host. That should expose grafana port to external world.
```console
kubectl port-forward svc/grafana --address=0.0.0.0 8888:80 2>&1 >/dev/null &
```
Credentials are admin:grafanapassword

## Environment and additional packages:
Following packages will be installed: Docker + containerd + minikube + helm + kubectl

## Underhood (infra)
Helm is used for application deployments.
```console
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install mysql bitnami/mysql --create-namespace -f values.yaml --namespace app --wait --timeout 10m0s --version 9.4.4
```
- For mysql - bitnami/mysql helm chart was used (version 9.4.4)
- For grafana - grafana/grafana (version 8.3.1)
- For prometheus - prometheus-community/prometheus (version 18.3.0)

In order to keep things simple, most of features and configs for these infrastracture services are disabled (no persistent volumes, no networkpolicies, no rbac-s, no tls), only required minimum left enabled. 
(for example, mysql replication is enabled)

app/infra - subdirectory contains all additional configuration for mysq, grafana, prometheus.
```console
(env) root@minikube:~/app# ls -la infra/
total 20
drwxr-xr-x 5 root root 4096 Nov 30 22:14 .
drwxr-xr-x 7 root root 4096 Dec  1 15:53 ..
drwxr-xr-x 2 root root 4096 Dec  1 12:22 grafana
drwxr-xr-x 2 root root 4096 Nov 30 22:14 mysql
drwxr-xr-x 2 root root 4096 Dec  1 15:17 prometheus
```
By default grafana is set to communicate with prometheus datasource. "k8s apps" dashboard in General folder with required metrics is configured as well.
Prometheus is configured to scrape metrics from pods containing `prometheus.io/scrape=true` annotations.

## Underhood (apps)
Applications' sources, as well as app and devops (helm charts, helm values, dockerfile) configs are stored in app/writer & app/reader subdirectories.
```console
(env) root@minikube:~/app/reader# ls -la 
total 28
drwxr-xr-x 5 root root 4096 Dec  1 09:16 .
drwxr-xr-x 7 root root 4096 Dec  1 15:53 ..
drwxr-xr-x 2 root root 4096 Dec  1 09:55 config
drwxr-xr-x 4 root root 4096 Dec  1 10:07 devops
-rw-r--r-- 1 root root   84 Nov 30 14:45 requirements.txt
-rw-r--r-- 1 root root   36 Nov 30 22:14 runner.py
drwxr-xr-x 4 root root 4096 Dec  1 15:54 src
```
There are no tests, or any security checks enabled during application deployment. In real environments tests, sec scans is a must.
There are no cicd tools involved in application deployment in the init.sh script. In real environments, cicd tools and software lifecycle must be introduced. 

In order to build image docker is used.
```console
docker build --no-cache -t localhost/reader:1.0.0 -f devops/docker/Dockerfile .
```
Images are stored locally and are loaded to minikube afterwords.
```console
minikube image load localhost/reader:1.0.0
```
Helm is used to deploy app in k8s minukube cluster
```console
helm install reader devops/helm/reader --create-namespace -n app
```
## Reader app
Python:3.7.15 is used for application development.
There are 3 replicas of app
```console
kubectl get ep -n app
NAME                       ENDPOINTS                                         AGE
reader                     172.17.0.7:8080,172.17.0.8:8080,172.17.0.9:8080   4h54m
```
Reader app connects to the mysql replica and counts number of rows in table and logs result to sdtout
```console
kubectl logs reader-b9ccb949d-65thf -n app --tail 10 -f
{"timestamp":"2022-12-01T20:18:34.000+0000", "level":"INFO", "thread": "MainThread", "message":"There are 14310 row(s) in the table"}
{"timestamp":"2022-12-01T20:18:35.000+0000", "level":"INFO", "thread": "MainThread", "message":"There are 14311 row(s) in the table"}
```
There are two enpoints available for reader app:
```console
tcp        0      0 0.0.0.0:9000            0.0.0.0:*               LISTEN      1/python3
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      1/python3
```
Port 9000 and path / is used for metric scraping (prometheus client_python library is used)
Port 8080 is used for api access. Api is located under /info path and it returns podname and rowsintable values (flask framework is used):
```console
curl http://192.168.49.2:31808/info
{
  "podname": "reader-b9ccb949d-65thf", 
  "rowsintable": [
    14485
  ]
}
```

## Writer App
Python:3.7.15 is used for application development.
There is one replica of writer application.
It connects to the mysql master server, creates tables if missing and commits random data to the created table. Outputs are logged to the stdout.
App generates random names,addresses and date to the `customers` table. (faker library is used)
```console
{"timestamp":"2022-12-01T20:30:59.000+0000", "level":"INFO", "thread": "MainThread", "message":"Generated name is Julie Long "}
{"timestamp":"2022-12-01T20:30:59.000+0000", "level":"INFO", "thread": "MainThread", "message":"Generated address is PSC 6175, Box 3990
APO AE 17845 "}
{"timestamp":"2022-12-01T20:30:59.000+0000", "level":"INFO", "thread": "MainThread", "message":"Generated delivery date is 2022-12-11"}
{"timestamp":"2022-12-01T20:30:59.000+0000", "level":"INFO", "thread": "MainThread", "message":"Commiting data Julie Long, PSC 6175, Box 3990
APO AE 17845, 2022-12-11 to database"}
```
Port 9000 and path / is used for metric scraping (prometheus client_python library is used)
Port 8080 is used for api access. Api is located under /info path and it returns podname (flask framework is used):
