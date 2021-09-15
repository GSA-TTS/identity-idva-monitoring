#!/bin/bash
set -e

download_output_file="prometheus.tar.gz"

# To update prometheus, update the download URL and checksum below.
# New versions can be found at https://prometheus.io/download/
download_url="https://github.com/prometheus/prometheus/releases/download/v2.30.0/prometheus-2.30.0.linux-amd64.tar.gz"
valid_hash="49c0809d4983f91c9afb8d260b36b821e90a6dcb82d0bad605ff9a3102a9e6d8  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
