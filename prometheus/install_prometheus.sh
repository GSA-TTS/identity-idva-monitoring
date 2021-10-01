#!/bin/bash
set -e

download_output_file="prometheus.tar.gz"

# To update prometheus, update the download URL and checksum below.
# New versions can be found at https://prometheus.io/download/
download_url="https://github.com/prometheus/prometheus/releases/download/v2.30.2/prometheus-2.30.2.linux-amd64.tar.gz"
valid_hash="1f5c239f6fa8da511ae140eea8d3190c1a6e0093247d758d81c99d63684ae1e1  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
