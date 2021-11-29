#!/bin/bash
set -e

version_num=$(cat VERSION)
download_output_file="grafana.tar.gz"
download_url="https://dl.grafana.com/oss/release/grafana-$version_num.linux-amd64.tar.gz"
# Get hash
valid_hash="$(curl -s "$download_url.sha256" | tr -d '\n') $download_output_file"

# Download the grafana archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing grafana.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
