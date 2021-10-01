#!/bin/bash
set -e

# To update alertmanager, simply update the version number below
version_num="0.23.0"
download_url="https://github.com/prometheus/alertmanager/releases/download/v$version_num"
archive_name="alertmanager-$version_num.linux-amd64.tar.gz"

archive_url="$download_url/$archive_name"
shasum_url="$download_url/sha256sums.txt"

# Download the Alertmanager archive and shasum file
wget --quiet "$archive_url"
wget --quiet "$shasum_url"

# Compare sha256sum
sha256sum --check --ignore-missing --status sha256sums.txt

# Extract the archive to the current directory, preserving the existing prometheus.yml
tar -xzf $archive_name --strip-components 1 --skip-old-files
rm "$archive_name" sha256sums.txt
