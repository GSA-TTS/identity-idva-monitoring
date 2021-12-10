#!/bin/bash
set -e

# To update Prometheus, simply update the version number below
version_num=$(cat VERSION)
download_url="https://github.com/prometheus/prometheus/releases/download/v$version_num"
archive_name="prometheus-$version_num.linux-amd64.tar.gz"
shasum_filename="sha256sums.txt"

archive_url="$download_url/$archive_name"
shasum_url="$download_url/$shasum_filename"

# Download the Prometheus archive and shasum file
wget --quiet "$archive_url"
wget --quiet "$shasum_url"

# Compare sha256sum
sha256sum --check --ignore-missing --status "$shasum_filename"

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf "$archive_name" --strip-components 1 --skip-old-files
rm "$archive_name" "$shasum_filename"
