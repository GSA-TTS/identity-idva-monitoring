#!/bin/bash
proxy_url=$(echo "$VCAP_SERVICES" | jq -r '."user-provided"?[]? | select(.name == "outbound-proxy") | .credentials.proxy_url')

# Export the proxy variables if the "proxy_url" variable is not empty
if [ -n "$proxy_url" ]; then
  export HTTP_PROXY="$proxy_url"
  export HTTPS_PROXY="$proxy_url"
  echo ".profile script automatically set HTTP_PROXY: $HTTP_PROXY"
  echo ".profile script automatically set HTTPS_PROXY: $HTTPS_PROXY"
else
  echo ".profile script did not find proxy information in VCAP_SERVICES"
fi
