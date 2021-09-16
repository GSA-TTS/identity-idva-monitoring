#!/bin/bash
{
    echo "---"
    echo "tls_server_config:"
    echo "  cert_file: $CF_INSTANCE_CERT"
    echo "  key_file: $CF_INSTANCE_KEY"
} > web-config.yml
