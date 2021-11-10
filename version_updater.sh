#!/bin/bash

# Updates the VERSION file for the tools being used within this repo. When a
# new release is published, this script will pull the version number from
# GitHub and update the VERSION file as necessary, as well as export the needed
# data for the update.yml workflow to open a PR for the change.

# Args:
#   $1 path to a VERSION file within this repo. For example "./prometheus/VERSION"
#   $2 GitHub API URL to the "/releases/latest" for the tool being used.

usage() {
  echo "./version_updater <path_to_version_file> <github_latest_release_url>"
  exit 1
}

if [[ ! -f "$1" ]] || [[ -z "$2" ]]; then
  usage
fi


# Do not allow arbitrary filenames to be specified
version_file_basename=$(basename "$1") 

# Returns number > 0 if the file is somewhere within the current (sub)directory
file_in_repo=$(find . -wholename "$1" | wc -l)

if [[ "$version_file_basename" != "VERSION" ]] || [[ "$file_in_repo" -eq 0 ]]; then
  echo "You specified something that doesn't look like a VERSION file."
  usage
fi

current_version=$(cat "$1")
echo "Found current version: $current_version"

latest_json=$(curl --silent "$2")
latest_version=$(echo "$latest_json" | jq -r .tag_name | tr -d 'v')
echo "Latest version available: $latest_version"

html_url=$(echo "$latest_json" | jq -r .html_url)
echo -n "$latest_version" > VERSION

{
  echo "CURRENT_VERSION=$current_version"
  echo "LATEST_VERSION=$latest_version"
  echo "HTML_URL=$html_url"
} >> "$GITHUB_ENV"
