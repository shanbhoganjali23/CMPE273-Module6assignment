# Kubernetes Inventory Service Lab

This project deploys an Inventory service with two Kubernetes replicas and a client that communicates with the service by using the stable Service name `inventory-service`.

## Architecture

```text
Client Pod → inventory-service → Inventory Pod 1
                            → Inventory Pod 2
```

The Inventory response includes the Pod name so that request distribution can be observed.

## Prerequisites

- Docker Desktop with Kubernetes enabled
- `kubectl`

In Docker Desktop, open **Kubernetes**, create a cluster, and wait until it is running. Verify it with:

```bash
kubectl get nodes
```

## Deploy the application

From the project directory, build the Inventory image and apply the Kubernetes configuration:

```bash
docker build -t inventory-service:1.0 ./app
kubectl apply -f k8s/inventory.yaml
kubectl rollout status deployment/inventory
kubectl rollout status deployment/inventory-client
```

Check the Pods and Service:

```bash
kubectl get pods -o wide
kubectl get service inventory-service
kubectl get endpoints inventory-service
```

## Test 1: Service discovery and replicas

The client uses `http://inventory-service:8080`, not a Pod IP. View its requests with:

```bash
kubectl logs deployment/inventory-client --tail=30
```

The output should show responses from both Inventory Pod names.

## Test 2: Readiness failure and recovery

Select one Inventory Pod:

```bash
BAD_POD=$(kubectl get pods -l app=inventory -o jsonpath='{.items[0].metadata.name}')
echo "$BAD_POD"
```

Make it fail readiness:

```bash
kubectl exec "$BAD_POD" -- python -c "import urllib.request; print(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/admin/fail-readiness', method='POST')).read().decode())"
sleep 5
kubectl get pods -l app=inventory
kubectl get endpoints inventory-service
kubectl logs deployment/inventory-client --tail=20
```

The Pod should still be running but show `0/1`, disappear from the Service endpoints, and stop receiving normal client traffic.

Restore readiness:

```bash
kubectl exec "$BAD_POD" -- python -c "import urllib.request; print(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/admin/restore-readiness', method='POST')).read().decode())"
sleep 5
kubectl get pods -l app=inventory
kubectl get endpoints inventory-service
kubectl logs deployment/inventory-client --tail=30
```

The Pod should return to `1/1` and appear in the Service endpoints again.

## Test 3: Pod deletion and replacement

Delete one Inventory Pod:

```bash
OLD_POD=$(kubectl get pods -l app=inventory -o jsonpath='{.items[0].metadata.name}')
echo "Deleting $OLD_POD"
kubectl delete pod "$OLD_POD"
kubectl get pods -l app=inventory -w
```

Press `Control+C` after the replacement Pod is running. Then run:

```bash
kubectl get pods -l app=inventory
kubectl get service inventory-service
kubectl logs deployment/inventory-client --tail=20
```

The replacement Pod should have a different name. The Service name should remain `inventory-service`, and the client should continue receiving responses.

## Evidence

The `evidence/` directory contains terminal output collected while testing:

- Both replicas receiving requests
- Readiness failure
- Readiness recovery
- Pod deletion and replacement

## Reflection

A stable Service name gives the client one reliable destination even when the Pods behind it change. Kubernetes automatically updates the Service endpoints as Pods become ready, fail readiness, or are replaced. The client does not need to know the individual Pod IP addresses or names. This makes communication more reliable during Pod failures and replacements.

## Cleanup

```bash
kubectl delete -f k8s/inventory.yaml
```
