#!/bin/bash
set -e

download_output_file="grafana.tar.gz"

# To update grafana, update the download URL and checksum below.
# New versions can be found at https://grafana.com/grafana/download
# in the 'Standalone Linux Binaries' section.
download_url="https://dl.grafana.com/oss/release/grafana-8.2.1.linux-amd64.tar.gz"
valid_hash="e238ec1f78369fc8f9c094584223d763a6e86a83cf33bcb7b0d750341dc2e988  $download_output_file"

# Download the grafana archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing grafana.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
