"""
This file is for analytics scripting, querying data from the dev-skevents-* index pattern
and placing the result in the dev-analytics-* index pattern for further visualizations
"""

import argparse
import sys
import requests
from opensearchpy import OpenSearch
import analyticsconstants
from analytics_query import CompositeAggregationQuery, ScanQuery
import queries


def get_command_line_arguments():
    """
    Returns command line argument names and values.
    """
    cmd_line_parser = argparse.ArgumentParser()
    cmd_line_parser.add_argument("--host")
    cmd_line_parser.add_argument("--port")
    cmd_line_parser.add_argument("--flow_id")
    cmd_line_parser.add_argument("--start_date", default=None)
    cmd_line_parser.add_argument("--end_date", default=None)
    cmd_line_parser.add_argument("--username")
    cmd_line_parser.add_argument("--password")
    cmd_line_parser.add_argument("--base_url")
    arguments = cmd_line_parser.parse_args()

    return arguments


def get_authorization_header_to_idva_flows(
    email: str, password: str, login_url: str
) -> dict:
    """
    Returns a header, containing an access token, for an http request to flow data.
    """
    # the required authentication to obtain an access token
    auth = {"email": email, "password": password}

    # the required access token for accessing flow data
    json = requests.post(login_url, data=auth).json()

    try:
        access_token = json["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    except KeyError:
        print(json)
        sys.exit(1)


def get_mappings(flow_id: str, email: str, password: str, base_url: str) -> dict:
    """
    Returns the mappings of flow id to flow name and node id to node names.
    """
    login_url = f"{base_url}/customers/login"

    header = get_authorization_header_to_idva_flows(email, password, login_url)
    # pulling out the flow data for a flow of a given flow id
    flow_url = f"{base_url}/v1/flows/{flow_id}"
    json = requests.get(flow_url, headers=header).json()
    try:
        flow = json["flowInfo"]
    except KeyError:
        print(json)
        sys.exit(1)
    # We always run the script with one specified flow id, so flows should always have one element
    nodes = flow["graphData"]["elements"]["nodes"]

    node_mappings = []
    for node in nodes:

        try:
            # the node title is defined
            node_title = node["data"]["properties"]["nodeTitle"]["value"]
        except KeyError:
            # the node title has not yet been defined
            continue

        # Only add the node id to title mapping if the title is defined for the node
        node_mappings.append(
            {
                "id": node["data"]["id"],
                "title": node_title,
            }
        )
    ids_names_mapping = {
        "flow_id": flow_id,
        "flow_name": flow["name"],
        "nodes": node_mappings,
    }
    return ids_names_mapping


def main() -> None:
    """
    The main method for running the script.
    """
    arguments = get_command_line_arguments()
    elasticsearch = OpenSearch(
        hosts=[{"host": arguments.host, "port": arguments.port}], timeout=300
    )

    mappings = get_mappings(
        arguments.flow_id,
        arguments.username,
        arguments.password,
        arguments.base_url,
    )

    kwargs = {
        "elasticsearch": elasticsearch,
        "index_pattern": analyticsconstants.EVENTS_INDEX_PATTERN,
        "query": queries.connector_pass_rate,
        "flow_id": arguments.flow_id,
        "event_message": "Connector Pass Rate",
        "metric": "connector_pass_rate",
        "metric_key": ["flowId", "interactionId", "id", "tsEms"],
        "num_composite_buckets": analyticsconstants.DEFAULT_NUM_COMPOSITE_BUCKETS,
        "document_keys": ["id", "connectionId", {"property": "outcomeStatus"}],
        "start_date": arguments.start_date,
        "end_date": arguments.end_date,
        "mappings": mappings,
    }

    connector_pass_rate = ScanQuery(**kwargs)
    connector_pass_rate.send_query_and_evaluate_results()
    kwargs["metric_key"] = ["interactionId", "id"]
    kwargs["event_message"] = "Connector Response Time"
    kwargs["metric"] = "connector_response_time"
    kwargs["query"] = queries.connector_response_time
    kwargs["index_pattern"] = analyticsconstants.SK_INDEX_PATTERN
    kwargs["document_keys"] = ["sessionLength"]

    connector_response_time = CompositeAggregationQuery(**kwargs)
    connector_response_time.send_query_and_evaluate_results()

    kwargs["metric_key"] = ["interactionId"]
    kwargs["event_message"] = "Interaction Response Time"
    kwargs["metric"] = "interaction_response_time"
    kwargs["query"] = queries.workflow_response_time
    kwargs["index_pattern"] = analyticsconstants.SK_INDEX_PATTERN
    kwargs["document_keys"] = ["sessionLength"]

    workflow_response_time = CompositeAggregationQuery(**kwargs)
    workflow_response_time.send_query_and_evaluate_results()


if __name__ == "__main__":
    main()
