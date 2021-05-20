#!/bin/bash
set -e

# Download the Prometheus archive
wget --quiet -O prometheus.tar.gz --input-file=prometheus_download_url.txt

valid_prometheus_shasum="ce637d0167d5e6d2561f3bd37e1c58fe8601e13e4e1ea745653c068f6e1317ae  prometheus.tar.gz"
if [[ "$(sha256sum prometheus.tar.gz)" !=  "$valid_prometheus_shasum" ]]; then
    echo "sha256sum failed validation"
    exit 1
fi

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf prometheus.tar.gz --strip-components 1 --skip-old-files
