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
cf add-network-policy elasticsearch-metrics es-proxy

# Source = Grafana
cf add-network-policy grafana cortex
cf add-network-policy grafana prometheus --protocol tcp --port 61443

# Source = Kibana
cf add-network-policy kibana es-proxy

# Source = Prometheus
cf add-network-policy prometheus alertmanager
cf add-network-policy prometheus cf-metrics
cf add-network-policy prometheus cortex
cf add-network-policy prometheus elasticsearch-metrics
cf add-network-policy prometheus grafana --port 61443 --protocol tcp
cf add-network-policy prometheus kong --port 8100 --protocol tcp
cf add-network-policy prometheus redis-metrics
cf add-network-policy prometheus watchtower
