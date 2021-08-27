#!/bin/bash
set -e

download_output_file="prometheus.tar.gz"

# To update prometheus, update the download URL and checksum below.
# New versions can be found at https://prometheus.io/download/
download_url="https://github.com/prometheus/prometheus/releases/download/v2.29.2/prometheus-2.29.2.linux-amd64.tar.gz"
valid_hash="51500b603a69cf1ea764b59a7456fe0c4164c4574714aca2a2b6b3d4da893348  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
