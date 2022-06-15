#!/bin/bash
# This script serves as a centralized location for creating all network
# policies required by apps contained within this repository. All GitHub
# actions to deploy the apps in this repo should use this script to
# create the required network policies instead of adding custom "run"
# scripts within the action.

if [ -z "$ENVIRONMENT_NAME" ]; then
  echo "No ENVIRONMENT_NAME variable found."
  exit 1
fi


# The base environment (dev|test|prod) will have the restricted-egress policies attached.
# See: https://cloud.gov/docs/management/space-egress/#restricted-egress
restricted="$ENVIRONMENT_NAME"
public="$restricted-public"
closed="$restricted-closed"

cf target -s "$restricted"

# Source = Idvametrics
cf add-network-policy idvametrics es-proxy --protocol tcp --port 8080 -s "$restricted"

# Source = Kibana
cf add-network-policy kibana es-proxy                  --protocol tcp --port 61443 -s "$restricted"

cf target -s "$closed"

cf add-network-policy watchtower outbound-proxy        --protocol tcp --port 61443 -s "$public"

# Source = Grafana
cf add-network-policy grafana cortex                   --protocol tcp --port 61443 -s "$restricted"
cf add-network-policy grafana prometheus               --protocol tcp --port 61443 -s "$closed"

# Source = Prometheus
cf add-network-policy prometheus alertmanager          --protocol tcp --port 61443 -s "$public"
cf add-network-policy prometheus cf-metrics            --protocol tcp --port 61443 -s "$restricted"
cf add-network-policy prometheus cortex                --protocol tcp --port 61443 -s "$restricted"
cf add-network-policy prometheus grafana               --protocol tcp --port 61443 -s "$closed"
cf add-network-policy prometheus elasticsearch-metrics --protocol tcp --port 61443 -s "$closed"
cf add-network-policy prometheus kong                  --protocol tcp --port 8100  -s "$closed"
cf add-network-policy prometheus redis-metrics         --protocol tcp --port 61443 -s "$restricted"
cf add-network-policy prometheus watchtower            --protocol tcp --port 61443 -s "$closed"

# Source = Elasticsearch-metrics
cf add-network-policy elasticsearch-metrics es-proxy   --protocol tcp --port 61443 -s "$restricted"

cf target -s "$public"

# Source = Alertmanager
cf add-network-policy alertmanager alertmanager        --protocol tcp --port 9094 -s "$public"
cf add-network-policy alertmanager alertmanager        --protocol udp --port 9094 -s "$public"
