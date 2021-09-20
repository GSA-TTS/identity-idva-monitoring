./install_alertmanager.sh

if [ -z "$ENVIRONMENT_NAME" ]; then
    echo "Error: empty ENVIRONMENT_NAME environment variable."
    exit
fi

./alertmanager --web.listen-address="0.0.0.0:$PORT" --cluster.peer="identity-idva-monitoring-alerts-$ENVIRONMENT_NAME.apps.internal:9094"
