#!/bin/bash
# This script serves as a centralized location for creating all network
# policies required by apps contained within this repository. All GitHub
# actions to deploy the apps in this repo should use this script to
# create the required network policies instead of adding custom "run"
# scripts within the action.

# Source = Alertmanager
cf add-network-policy alertmanager alertmanager --protocol tcp --port 9094
cf add-network-policy alertmanager alertmanager --protocol udp --port 9094

# Source = Elasticsearch-metrics
cf add-network-policy elasticsearch-metrics es-proxy --protocol tcp --port 61443

# Source = Grafana
cf add-network-policy grafana cortex     --protocol tcp --port 61443
cf add-network-policy grafana prometheus --protocol tcp --port 61443

# Source = Kibana
cf add-network-policy kibana es-proxy --protocol tcp --port 61443

# Source = Prometheus
cf add-network-policy prometheus alertmanager          --protocol tcp --port 61443
cf add-network-policy prometheus cf-metrics            --protocol tcp --port 61443
cf add-network-policy prometheus cortex                --protocol tcp --port 61443
cf add-network-policy prometheus grafana               --protocol tcp --port 61443 
cf add-network-policy prometheus elasticsearch-metrics --protocol tcp --port 61443
cf add-network-policy prometheus kong                  --protocol tcp --port 8100
cf add-network-policy prometheus redis-metrics         --protocol tcp --port 61443
cf add-network-policy prometheus watchtower            --protocol tcp --port 61443

# Source = Analytics Scripting
cf add-network-policy analytics-scripting es-proxy --protocol tcp --port 61443
