#!/bin/bash
proxy_url=$(echo "$VCAP_SERVICES" | jq '.["user-provided"][] | select(.name == "outbound-proxy") | .credentials.proxy_url')

# Export the proxy variables if the "proxy_url" variable is not empty
if [ -n "$proxy_url" ]; then
  export HTTP_PROXY=$proxy_url
  export HTTPS_PROXY=$proxy_url
fi
