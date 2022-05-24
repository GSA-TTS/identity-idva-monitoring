"""
Provides utility functions for use in analytics scripting.
"""

from datetime import datetime, timedelta
import sys
from typing import Callable
from dateutil import parser
import requests


def convert_date_to_timestamp(
    date: str = None,
    time_delta: timedelta = timedelta(0),
    get_recent_timestamp: Callable[[], datetime] = None,
) -> int:
    """
    Converts a string formatted date to an int timestamp representing the date.
    """
    if date:
        return int((parser.parse(date) - time_delta).timestamp())

    if get_recent_timestamp:
        return int(get_recent_timestamp() - time_delta)

    return int(datetime.now().timestamp())


def create_bulk_delete_action(index: str, document_id: str) -> dict:
    """
    Creates an individual Bulk API delete action.
    """
    return {
        "_op_type": "delete",
        "_index": index,
        "_type": "_doc",
        "_id": document_id,
    }


def create_bulk_index_action(
    index_to_update: str, document_id: str, document: dict
) -> dict:
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
    login_url = f"{base_url}/v1/customers/login"

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


def update_nested_key(dictionary: dict, key_path: list, value: dict) -> None:
    """
    Updates a dictionary at the nested key defined by key_path with value, adding
    the nested keys if they do not exist
    """
    curr_dict = dictionary
    for key in key_path:
        curr_dict = curr_dict.setdefault(key, {})

    curr_dict.update(value)
