#!/bin/bash -e

# To update Cortex, simply update the version number below
version_num="1.10.0"
download_url="https://github.com/cortexproject/cortex/releases/download/v$version_num/"
archive_name="cortex-linux-amd64"

archive_url="$download_url/$archive_name"
shasum_name="$archive_name-sha-256"
shasum_url="$download_url/$shasum_name"

# Download the Prometheus archive and shasum file
wget --quiet "$archive_url"
wget --quiet "$shasum_url"

# Compare sha256sum
sed -i "s/$/  $archive_name/" "$shasum_name"
sha256sum --check --ignore-missing --status "$shasum_name"

# Add executable permissions
chmod +x $archive_name
