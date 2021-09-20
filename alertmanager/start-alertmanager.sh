./install_alertmanager.sh

if [ -z "$ENVIRONMENT_NAME" ]; then
    echo "Error: empty ENVIRONMENT_NAME environment variable."
    exit
fi

echo "My IP is: $CF_INSTANCE_INTERNAL_IP"

if [[ $CF_INSTANCE_INDEX == 0 ]]; then
    # HA leader node. Peers will specify this node in their --cluster.peer list
    ./alertmanager --web.listen-address="0.0.0.0:$PORT"
else
    # Additional HA instances
    sleep 10 # Allow time for leader to launch

    # host performs a dns lookup for the domain name. grep & awk pull out the addess returned
    peer_list=$(host identity-idva-monitoring-dev.apps.internal | grep address | awk '{ print $4 }' | sed 's/$/:9094 /' | sed 's/^/--cluster.peer=/')
    peer_list=$(echo -e "$peer_list" | tr -d '\n')
    echo "Peer list: $peer_list"

    sleep 5 # Give a small amount of buffer time for all additional HA instances to complete looking up leader ip

    ./alertmanager --web.listen-address="0.0.0.0:$PORT" "$peer_list"
fi
