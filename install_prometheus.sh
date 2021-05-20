#!/bin/bash
set -e

# To update prometheus, update the download URL and checksum found at https://prometheus.io/download/
prometheus_download_url="https://github.com/prometheus/prometheus/releases/download/v2.27.1/prometheus-2.27.1.linux-amd64.tar.gz"
prometheus_sha256sum="ce637d0167d5e6d2561f3bd37e1c58fe8601e13e4e1ea745653c068f6e1317ae  prometheus.tar.gz"

# Download the Prometheus archive
download_output_file="prometheus.tar.gz"
wget --quiet --output-document "$download_output_file" "$prometheus_download_url"

# Compare sha256sum
download_hash="$(sha256sum "$download_output_file")"

if [[ "$download_hash" != "$prometheus_sha256sum" ]]; then
    echo "sha256sum failed validation"
    exit 1
fi

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
