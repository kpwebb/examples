#!/bin/bash
curl localhost:9070/deployments -H 'content-type: application/json' -d '{"uri": "http://localhost:9080"}'
curl localhost:9070/deployments -H 'content-type: application/json' -d '{"uri": "http://localhost:9081"}'

sleep 3
curl localhost:9070/subscriptions -H 'content-type: application/json' -d '{ "source":"kafka://my-cluster/orders", "sink":"service://OrderWorkflow/create" }'
curl localhost:9070/subscriptions -H 'content-type: application/json' -d '{ "source":"kafka://my-cluster/driver-updates", "sink":"service://DriverDigitalTwin/handleDriverLocationUpdateEvent" }'

sleep 3

curl -X POST localhost:8080/DriverMobileAppSimulator/driver-A/startDriver
curl -X POST localhost:8080/DriverMobileAppSimulator/driver-B/startDriver