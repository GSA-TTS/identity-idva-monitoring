"""
Script for retrieving the mapping of flow ids to flow names and nodes ids to node titles.
"""

import argparse
from datetime import datetime
from hashlib import sha256
import requests
from opensearchpy import OpenSearch, helpers

ANALYTICS_INDEX_PATTERN = "dev-analytics"


def create_bulk_index_action(index_to_update: str, document_id: str, document: dict):
    """
    Creates an individual Bulk API index action.
    """
    return {
        "_index": index_to_update,
        "_type": "_doc",
        "_id": document_id,
        "_source": document,
        "_op_type": "index",
    }


def create_mapping_document(
    flow_id: str, flow_name: str, node_id: str, node_title: str
):
    """
    Creates a document containing the flow id to flow title and node id to node title mappings.
    """
    return {
        "flowId": flow_id,
        "flowName": flow_name,
        "nodeId": node_id,
        "nodeTitle": node_title,
    }


def create_document_id(flow_id: str, node_id: str) -> str:
    """
    Creates a document id, which depends on a flow and node id.
    """
    document_id = f"{flow_id}-{node_id}".encode()
    return sha256(document_id).hexdigest()


def create_mappings(flows: list):
    """
    Takes in a set of flows and adds the mappings to bulk index documents, returning the set of
    bulk actions.
    """

    bulk_actions = []

    # Going through the flows and pulling out the flow id, flow name, as well as the node id and
    # node title for all nodes in the flow.
    for flow in flows:
        flow_name = flow["name"]
        flow_id = flow["flowId"]
        nodes = flow["graphData"]["elements"]["nodes"]
        for node in nodes:
            node_id = node["id"]
            try:
                # the node title is defined
                node_title = node["data"]["properties"]["nodeTitle"]["value"]
            except KeyError:
                # the node title has not yet been defined
                node_title = None

            if node_title:
                # Only add the node id to title mapping if the title is defined for the node
                document = create_mapping_document(
                    flow_id, flow_name, node_id, node_title
                )
                document_id = create_document_id(flow_id, node_id)
                # the index the data is added to depends on the current date
                index_to_update = \
                  f'{ANALYTICS_INDEX_PATTERN}-{datetime.now().date().strftime("%Y.%m.%d")}'
                bulk_action = create_bulk_index_action(
                    index_to_update, document_id, document
                )
                bulk_actions.append(bulk_action)
    return bulk_actions


def main():
    """
    Makes necessary requests to obtain the mapping data and adds that data to the analytics index.
    """
    cmd_line_parser = argparse.ArgumentParser()
    cmd_line_parser.add_argument("--host")
    cmd_line_parser.add_argument("--port")
    cmd_line_parser.add_argument("--flow_ids", default="all")
    arguments = cmd_line_parser.parse_args()

    elasticsearch = OpenSearch(hosts=[{"host": arguments.host, "port": arguments.port}])
    flow_ids = arguments.flow_ids
    bulk_actions = []

    # url to all idva flows
    idva_flows_url = "https://idva-api-dev.app.cloud.gov/v1/flows"
    # the required authentication to obtain an access token
    auth = {"email": "idva@gsa.gov", "password": "vBtCVyI@v0oqgxBejd!sJz&ZJc"}
    # the url for logging in and obtaining an access token
    login_url = "https://idva-api-dev.app.cloud.gov/v1/customers/login"

    # the required access token for accessing flow data
    access_token = requests.post(login_url, data=auth).json()["access_token"]
    header = {"Authorization": f"Bearer {access_token}"}

    # pulling out the flow data for all flows
    flows = requests.get(idva_flows_url, headers=header).json()["flowsInfo"]
    # keeping only the specified flows
    flows = [
        flow
        for flow in flows
        if flow_ids == "all" or flow["flowId"] in flow_ids.split(",")
    ]

    bulk_actions = create_mappings(flows)

    # sending the mapping data to elasticsearch
    helpers.bulk(elasticsearch, bulk_actions)


if __name__ == "__main__":
    main()
