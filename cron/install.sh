#!/bin/bash
set -e

version_num=$(cat VERSION)
download_url="https://github.com/aptible/supercronic/releases/download/v$version_num"
file_name="supercronic-linux-amd64"

wget --quiet "$download_url/$file_name"

# Compare sha1sum
sha1sum --check sha1sum

mv "$file_name" supercronic
chmod +x supercronic

username=$(echo "$VCAP_SERVICES" | jq -r '.["cloud-gov-service-account"][0].credentials.username')
password=$(echo "$VCAP_SERVICES" | jq -r '.["cloud-gov-service-account"][0].credentials.password')
api=$(echo "$VCAP_APPLICATION" | jq -r '.cf_api')
org=$(echo "$VCAP_APPLICATION" | jq -r '.organization_name')
space=$(echo "$VCAP_APPLICATION" | jq -r '.space_name')

cf --version
cf api "$api"
cf auth "$username" "$password"
cf target -o "$org" -s "$space"
