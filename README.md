# promport

Simple HTTP server for uploading bulk data to Prometheus.

Intended to deploy as a sidecar container.

## Building

```
kubectl apply -f build.yaml
```

## Usage

```
DATA=<tsdb-dir> python3 -m promport
```
