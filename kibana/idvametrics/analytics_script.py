"""
This file is for analytics scripting, querying data from the dev-skevents-* index pattern
and placing the result in the dev-analytics-* index pattern for further visualizations
"""

import argparse
from datetime import datetime, timedelta
from dateutil import parser
from opensearchpy import OpenSearch, helpers

ANALYTICS_INDEX_PATTERN = "dev-analytics"
SK_INDEX_PATTERN = "dev-skevents-*"
DEFAULT_NUM_COMPOSITE_BUCKETS = 10
FIVE_MINS = timedelta(minutes=5)

query_avg_response_time = {
    "query": {
        "bool": {
            "must": [{"match_phrase": {"flowId": {}}}, {"range": {"tsEms": {}}}],
            "filter": [{"match_all": {}}],
        }
    },
    "_source": ["companyId", "flowId"],
    "size": 1,
    "aggs": {
        "composite_buckets": {
            "aggs": {
                "min": {"min": {"field": "tsEms"}},
                "max": {"max": {"field": "tsEms"}},
                "sessionLength": {
                    "bucket_script": {
                        "buckets_path": {"startTime": "min", "endTime": "max"},
                        "script": "params.endTime - params.startTime",
                    }
                },
            },
            "composite": {
                "sources": [{"agg": {"terms": {"field": "interactionId.keyword"}}}]
            },
        },
    },
}


def update_nested_key(dictionary: dict, key_path: list, value: dict):
    """
    Updates a dictionary at the nested key defined by key_path with value, adding
    the nested keys if they do not exist
    """
    curr_dict = dictionary
    for key in key_path:
        curr_dict = curr_dict.setdefault(key, {})

    curr_dict.update(value)


def get_most_recent_timestamp(flow_id: str):
    """
    We want to retrieve all data from dev-skevents with a timestamp at any time or more recent
    than 5 minutes before the timestamp of the most recent data in dev-analytics-*. This
    ensures that we do not miss any data.
    """

    newest_timestamp_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {"flowId": flow_id},
                    },
                ],
            },
        },
        "size": 1,
        "sort": [
            {
                "tsEms": {"order": "desc"},
            },
        ],
    }

    res = elasticsearch.search(
        index=f"{ANALYTICS_INDEX_PATTERN}-*", body=newest_timestamp_query
    )
    try:
        # Attempting to get the time of five minutes prior to the most recent timestamp (tsEms)
        # of a document in the analytics index.
        most_recent_timestamp = parser.parse(res["hits"]["hits"][0]["_source"]["tsEms"])
        five_mins_prior = most_recent_timestamp - FIVE_MINS
        return int(five_mins_prior.timestamp())
    except KeyError:
        # There is nothing in the analytics index for the given flow_id, so we want the timestamp
        # of five minutes prior to the current time.
        current_timestamp = (datetime.now() - FIVE_MINS).timestamp()
        return int(current_timestamp)


def create_index(new_index: str):
    """
    If we do not have an index titled new_index, we must create it.
    """
    if not elasticsearch.indices.exists(new_index):
        elasticsearch.indices.create(index=new_index)


def create_analytics_document(bucket: dict, source: dict, max_date: datetime):
    """
    Returns an Elasticsearch document which will be uploaded to the dev-analytics-* index pattern.
    """
    return {
        "doc_count": bucket["doc_count"],
        "min_date": parser.parse(bucket["min"]["value_as_string"]),
        "max_date": max_date,
        "sessionLength": bucket["sessionLength"]["value"],
        "companyId": source["companyId"],
        "flowId": source["flowId"],
        "eventMessage": "Interaction Response Time",
    }


def create_bulk_action(index_to_update: str, document_id: str, document: dict):
    """
    Creates an individual bulk action for use in a bulk request.
    """
    return {
        "_index": index_to_update,
        "_type": "_doc",
        "_id": document_id,
        "_source": document,
        "_op_type": "index",
    }


def process_composite_aggregation_data(query_result: dict):
    """
    Processes results from the composite aggregation query, sends data fetched from the result to
    the appropriate index using a bulk request, and prepares for further processing of composite
    query results.
    """
    buckets = query_result["aggregations"]["composite_buckets"]["buckets"]
    source = query_result["hits"]["hits"][0]["_source"]

    bulk_actions = []
    for bucket in buckets:
        # The document belongs in the analytics index defined by the max_date.
        max_date = parser.parse(bucket["max"]["value_as_string"])
        index_to_update = f"{ANALYTICS_INDEX_PATTERN}-{max_date.strftime('%Y.%m.%d')}"

        # If index_to_update has not yet been created, we must do so before sending it any
        # requests.
        create_index(index_to_update)

        document = create_analytics_document(bucket, source, max_date)
        document_id = bucket["key"]["agg"]

        bulk_action = create_bulk_action(index_to_update, document_id, document)
        bulk_actions.append(bulk_action)
    # sending the bulk request to Elasticsearch
    helpers.bulk(elasticsearch, bulk_actions)

    # "after_key" is the identifier of the last returned bucket and will be used to return the
    # next num_composite_buckets in the composite aggregation ordering.
    after_key = query_result["aggregations"]["composite_buckets"]["after_key"]["agg"]
    return after_key


def send_query_and_evaluate_result(
    query: dict,
    num_composite_buckets: int,
    start_date: str,
    end_date: str,
    flow_id: str,
):
    """
    Prepares query of Elasticsearch data for a given time range, sends the query, and
    processes each bucket of the query result in a separate function.
    """

    if start_date:
        # A start date was provided when running the script
        query_start_date = int(parser.parse(start_date).timestamp())
    elif not elasticsearch.indices.get_alias(f"{ANALYTICS_INDEX_PATTERN}-*"):
        # A start date was not provided when running the script and
        # the dev-analytics index doesn't exist
        query_start_date = int((datetime.now() - FIVE_MINS).timestamp())
    else:
        # A start date was not provided when running the script and
        # the dev-analytics index does exist
        query_start_date = get_most_recent_timestamp(flow_id)

    if end_date:
        # An end date was provided when running the script
        query_end_date = int(parser.parse(end_date).timestamp())
    else:
        # An end date was not provided when running the script
        query_end_date = int(datetime.now().timestamp())

    # setting the number of buckets we want to view at a time for the composite aggregation
    size = {"size": num_composite_buckets}
    update_nested_key(query, ["aggs", "composite_buckets", "composite"], size)

    # setting the queried flowId and required time range
    match_phrase = {"match_phrase": {"flowId": {"query": flow_id}}}
    query_range = {
        "range": {
            "tsEms": {
                "gte": query_start_date,
                "lte": query_end_date,
                "format": "epoch_second",
            }
        }
    }
    must = {
        "must": [match_phrase, query_range],
    }
    update_nested_key(query, ["query", "bool"], must)

    # running the query against dev-skevents in elasticsearch
    query_result = elasticsearch.search(index=SK_INDEX_PATTERN, body=query)

    # processing and querying additional composite aggregation buckets until there are no more
    # buckets to process.
    while (
        len(query_result["aggregations"]["composite_buckets"]["buckets"])
        == num_composite_buckets
    ):
        query_after_key = process_composite_aggregation_data(query_result)
        query_composite = query["aggs"]["composite_buckets"]["composite"]
        query_composite["after"] = {"agg": query_after_key}

        query_result = elasticsearch.search(index=SK_INDEX_PATTERN, body=query)

    # processing the last set of composite aggregation buckets, if there are any to process.
    if query_result["aggregations"]["composite_buckets"]["buckets"]:
        process_composite_aggregation_data(query_result)


cmd_line_parser = argparse.ArgumentParser()
cmd_line_parser.add_argument("--host")
cmd_line_parser.add_argument("--port")
cmd_line_parser.add_argument("--flow_id")
cmd_line_parser.add_argument("--start_date", default=None)
cmd_line_parser.add_argument("--end_date", default=None)
arguments = cmd_line_parser.parse_args()

elasticsearch = OpenSearch(hosts=[{"host": arguments.host, "port": arguments.port}])

send_query_and_evaluate_result(
    query_avg_response_time,
    DEFAULT_NUM_COMPOSITE_BUCKETS,
    arguments.start_date,
    arguments.end_date,
    arguments.flow_id,
)
