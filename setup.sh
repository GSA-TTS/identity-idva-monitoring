#!/bin/bash
set -e

# Download the Prometheus archive
wget --quiet -O prometheus.tar.gz https://github.com/prometheus/prometheus/releases/download/v2.27.1/prometheus-2.27.1.linux-amd64.tar.gz

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf prometheus.tar.gz --strip-components 1 --skip-old-files
