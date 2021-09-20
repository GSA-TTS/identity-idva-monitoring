#!/bin/bash
set -e

download_output_file="alertmanager.tar.gz"

# To update alertmanager, update the download URL and hash below.
download_url="https://github.com/prometheus/alertmanager/releases/download/v0.23.0/alertmanager-0.23.0.linux-amd64.tar.gz"
valid_hash="77793c4d9bb92be98f7525f8bc50cb8adb8c5de2e944d5500e90ab13918771fc  $download_output_file"

# Download the Prometheus archive
wget --quiet --output-document "$download_output_file" "$download_url"

# Compare sha256sum
echo "$valid_hash" | sha256sum --check --quiet

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$download_output_file" --strip-components 1 --skip-old-files
rm "$download_output_file"
