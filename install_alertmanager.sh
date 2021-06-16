#!/bin/bash
set -e

mkdir -p alerts
cd alerts

download_output_file="alertmanager.tar.gz"

# To update alertmanager, update the download URL and hash below.
download_url="https://github.com/prometheus/alertmanager/releases/download/v0.22.2/alertmanager-0.22.2.linux-amd64.tar.gz"
valid_hash="9c3b1cce9c74f5cecb07ec4a636111ca52696c0a088dbaecf338594d6e55cd1a  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
