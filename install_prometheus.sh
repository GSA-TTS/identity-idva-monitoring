#!/bin/bash
set -e

download_output_file="prometheus.tar.gz"

# To update prometheus, update the download URL and checksum below.
# New versions can be found at https://prometheus.io/download/
download_url="https://github.com/prometheus/prometheus/releases/download/v2.28.0/prometheus-2.28.0.linux-amd64.tar.gz"
valid_hash="d2d0ded275090a13208114b633abe41c40e14c83ff5ec07230d79b4da1d8e701  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
