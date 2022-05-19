#!/bin/bash
# See https://docs.cloudfoundry.org/devguide/deploy-apps/instance-identity.html
# for information on Cloud Foundry Instance Identity Credentials.
{
  echo "---"
  echo "tls_server_config:"
  echo "  cert_file: $CF_INSTANCE_CERT"
  echo "  key_file: $CF_INSTANCE_KEY"
  echo "tls_client_config:"
  echo "  ca_file: /etc/cf-system-certificates/trusted-ca-1.crt"
} > tls-config.yml
