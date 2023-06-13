#!/bin/bash
set -e

username=$(echo "$VCAP_SERVICES" | jq -r '.["cloud-gov-service-account"][0].credentials.username')
password=$(echo "$VCAP_SERVICES" | jq -r '.["cloud-gov-service-account"][0].credentials.password')
api=$(echo "$VCAP_APPLICATION" | jq -r '.cf_api')
org=$(echo "$VCAP_APPLICATION" | jq -r '.organization_name')
space=$(echo "$VCAP_APPLICATION" | jq -r '.space_name')

cf --version
cf api "$api"
cf auth "$username" "$password"
cf target -o "$org" -s "$space"

./supercronic crontab