#!/bin/bash -e

# To update Watchtower, simply update the version number in the VERSION file
version_num=$(cat VERSION)
download_url="https://github.com/18F/watchtower/releases/download/v$version_num"
binary_name="watchtower-$version_num.linux-amd64"
archive_name="$binary_name.tar.gz"
shasum_filename="sha256sums.txt"

archive_url="$download_url/$archive_name"
shasum_url="$download_url/$shasum_filename"

# Download the Watchtower archive and shasum file
wget --quiet "$archive_url"
wget --quiet "$shasum_url"

# Compare sha256sum
sha256sum --check --ignore-missing --status "$shasum_filename"

# Extract and clean up
tar -xzf "$archive_name"
rm "$archive_name" "$shasum_filename"
mv "$binary_name" watchtower
