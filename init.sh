#!/bin/bash
set +ex

#Setup docker
apt-get update
apt-get install ca-certificates curl gnupg lsb-release -y

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install docker-ce docker-ce-cli containerd.io -y


#Setup minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
install minikube-linux-amd64 /usr/local/bin/minikube

minikube config set driver docker
minikube start --driver=docker --force

#Setup helm
wget https://get.helm.sh/helm-v3.10.2-linux-amd64.tar.gz
tar -zxvf helm-v3.10.2-linux-amd64.tar.gz
mv linux-amd64/helm /usr/local/bin/helm
helm version

#Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version


#Build docker images
workdir=$(pwd)
cd ${workdir}/reader
docker build --no-cache -t localhost/reader:1.0.0 -f devops/docker/Dockerfile .

cd ${workdir}/writer
docker build --no-cache -t localhost/writer:1.0.0 -f devops/docker/Dockerfile .

cd ${workdir}

#Push image to minikube
minikube image load localhost/reader:1.0.0
minikube image load localhost/writer:1.0.0

#Deploy infrastructure

cd ${workdir}/infra/mysql
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install mysql bitnami/mysql --create-namespace -f values.yaml --namespace app --wait --timeout 10m0s --version 9.4.4

cd ${workdir}/infra/prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -f values.yaml --wait --timeout 10m0s --version 18.3.0

cd ${workdir}/infra/grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -f values.yaml --wait --timeout 10m0s --version 6.44.11


#Deploy apps
cd ${workdir}/reader
helm install reader devops/helm/reader --create-namespace -n app

cd ${workdir}/writer
helm install writer devops/helm/writer --create-namespace -n app


