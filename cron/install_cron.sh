#!/bin/bash
set -e

version_num=$(cat VERSION)
download_url="https://github.com/aptible/supercronic/releases/download/v$version_num"
file_name="supercronic-linux-amd64"

wget --quiet "$download_url/$file_name"

# Compare sha1sum
sha1sum --check sha1sum

mv "$file_name" supercronic
chmod +x supercronic
