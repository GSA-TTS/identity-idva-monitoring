web_config_name="web-config.yml"

# Generate config files
envsubst < prometheus-config.yml > prometheus.yml
envsubst < web-config-template.yml > "$web_config_name"

./prometheus \
  --web.listen-address="0.0.0.0:$PORT" \
  --storage.tsdb.retention.size="950MB" \
  --web.config.file="$web_config_name" \
  --web.external-url https://identity-idva-monitoring-prometheus-"$ENVIRONMENT_NAME".apps.internal/
