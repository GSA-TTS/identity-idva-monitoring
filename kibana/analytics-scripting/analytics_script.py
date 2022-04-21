"""
This file is for analytics scripting, querying data from the dev-skevents-* index pattern
and placing the result in the dev-analytics-* index pattern for further visualizations
"""

import argparse
from datetime import datetime, timedelta
from dateutil import parser
from opensearchpy import OpenSearch, helpers

ANALYTICS_INDEX_PATTERN = "dev-skanalytics-*"
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
    "size": 0,
    "aggs": {
        "my_buckets": {
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
        "hits": {"top_hits": {"_source": ["companyId", "flowId"], "size": 1}},
    },
}

def add_keys_if_not_exist(dictionary: dict, keys: list):
    """
    Adds keys, in a nested format, to the dictionary if the keys do not exist.
    """
    curr_dict = dictionary
    for key in keys:
        curr_dict.setdefault(key, {})
        curr_dict = curr_dict[key]

def get_most_recent_timestamp(flow_id: str):
    """
    We want to retrieve all data from dev-skevents with a timestamp at any time or more recent
    than 5 minutes before the timestamp of the most recent data in dev-analytics-*. This
    ensures that we do not miss any data.
    """

    newest_timestamp_query = {
        "query": {
            "bool": {
                "must": [{"match_phrase": {"flowId": {"query": flow_id}}}],
                "filter": [{"match_all": {}}],
            }
        },
        "size": 0,
        "aggs": {
            "types_count": {
                "top_hits": {"size": 1, "sort": [{"tsEms": {"order": "desc"}}]}
            }
        },
    }

    res = elasticsearch.search(index=ANALYTICS_INDEX_PATTERN, body=newest_timestamp_query)
    try:
        most_recent_timestamp = parser.parse(
            res["aggregations"]["types_count"]["hits"]["hits"][0]["_source"]["tsEms"]
        )
        five_mins_prior = most_recent_timestamp - FIVE_MINS
        return int(five_mins_prior.timestamp())
    except KeyError:
        current_timestamp = (datetime.now() - FIVE_MINS).timestamp()
        return int(current_timestamp)

def create_index_if_doesnt_exist(new_index: str):
    """
    If we do not have an index of type prefix for a given date, we must create it.
    """
    if not elasticsearch.indices.exists(new_index):
        elasticsearch.indices.create(index=new_index)

def create_documents_and_send_bulk_request(buckets: list, source: dict):
    """
    Given the buckets returned from the composite aggregation query, fetch the appropriate data
    from each bucket, create an elasticsearch document using that data, and create the single
    bulk request for that document. Once all documents and corresponding requests have been
    created, send the bulk request to the elasticsearch cluster.
    """
    bulk_actions = []
    for bucket in buckets:
        # Should we go through past indices and attempt deletes so the interactionId doesn't
        # appear in multiple indices? The index of the bulk request only applies to the specific
        # index we're attempting to update

        # The document, identified by its interactionId, created from the current bucket belongs
        # in the index defined by the latest date (max_date) of which the interactionId appears.
        # The index is defined by index_to_update and is determined by max_date.
        max_date = parser.parse(bucket["max"]["value_as_string"])
        index_to_update = f"dev-analytics-{max_date.strftime('%Y.%m.%d')}"

        # If index_to_update has not yet been created, we must do so before sending it any
        # requests.
        create_index_if_doesnt_exist(index_to_update)

        # creating the document that is sent with the bulk request and added to the index_to_update
        # index
        document = {
            "doc_count": bucket["doc_count"],
            "min_date": parser.parse(bucket["min"]["value_as_string"]),
            "max_date": max_date,
            "sessionLength": bucket["sessionLength"]["value"],
            "companyId": source["companyId"],
            "flowId": source["flowId"],
            "eventMessage": "Interaction Response Time",
        }

        # creating the single bulk action along with the document, which is
        # stored under "_source"
        bulk_action = {
            "_index": index_to_update,
            "_type": "_doc",
            "_id": bucket["key"]["agg"],
            "_source": document,
            "_op_type": "index",
        }

        bulk_actions.append(bulk_action)
    # sending the bulk request to Elasticsearch
    helpers.bulk(elasticsearch, bulk_actions)

def process_composite_aggregation_data(query_result: dict):
    """
    Obtains necessary data for sending the Bulk API request that updates the
    appropriate indices with the new data. Then prepares for obtaining the next
    num_composite_buckets buckets from the composite aggregation result.
    """
    buckets = query_result["aggregations"]["my_buckets"]["buckets"]
    source = query_result["aggregations"]["hits"]["hits"]["hits"][0]["_source"]

    create_documents_and_send_bulk_request(buckets, source)
    # Composite aggregation queries only return a specified number of buckets,
    # num_composite_buckets in our case. The ordering of the buckets in the
    # composite query is done by the "sources" property. Each time a composite
    # query is run, it will return a key idenitifying the last returned bucket in
    # the composite aggregation ordering. This key is placed into the "after_key"
    # variable in this script. That variable is then used in running subsequent
    # composite aggregation queries, in which we are obtaining additional
    # composite aggregation buckets that we could not get from previous queries.
    # When we add, or update, the "after":{"agg":after_key} structure to the
    # composite aggregation portion of the query, we are telling elasticsearch
    # to return the next num_composite_buckets, as defined by the composite
    # aggregation ordering, from the set of all composite aggregation buckets.

    query_composite = query_avg_response_time["aggs"]["my_buckets"]["composite"]
    after_key = query_result["aggregations"]["my_buckets"]["after_key"]["agg"]

    query_composite.setdefault("after", {})
    query_composite["after"] = {"agg": after_key}

def send_query_and_evaluate_result(
    es_cluster: OpenSearch,
    query: dict,
    num_composite_buckets: int,
    args: argparse.ArgumentParser
):
    """
    Prepares query of Elasticsearch data for a given time range, sends the query, and
    processes each bucket of the query result in a separate function.
    """
    #Raises an AttributeError if not provided
    flow_id = args.flowId

    try:
        start_date = int(parser.parse(args.startDate).timestamp())
    except AttributeError:
        if not elasticsearch.indices.get_alias(ANALYTICS_INDEX_PATTERN):
            # The dev-skanalytics index doesn't exist, so we want 5 minutes before the current time
            start_date = int((datetime.now() - FIVE_MINS).timestamp())
        else:
            start_date = get_most_recent_timestamp(flow_id)

    try:
        end_date = int(parser.parse(args.endDate).timestamp())
    except AttributeError:
        end_date = int(datetime.now().timestamp())

    # setting the number of buckets we want to view at a time for the composite aggregation
    add_keys_if_not_exist(query, ["aggs","my_buckets", "composite", "size"])
    query["aggs"]["my_buckets"]["composite"]["size"] = num_composite_buckets

    # adding keys if they do not exist, preventing any KeyErrors
    add_keys_if_not_exist(query, ["query","bool"])
    query["query"]["bool"].setdefault("must", [{},{}])

    must = query["query"]["bool"]["must"]
    add_keys_if_not_exist(must[0], ["match_phrase", "flowId"])
    add_keys_if_not_exist(must[1], ["range", "tsEms"])

    # querying the flow with the specified flowId
    must[0]["match_phrase"]["flowId"] = {"query": flow_id}

    # specifying a date range for the query
    must[1]["range"]["tsEms"] = {
        "gte": start_date,
        "lte": end_date,
        "format": "epoch_second",
    }

    # running the query against dev-skevents in elasticsearch
    query_result = es_cluster.search(index=SK_INDEX_PATTERN, body=query)
    # len(query_result["aggregations"]["my_buckets"]["buckets"]) is the number of buckets
    # in the composite aggregation. If the number of buckets in the composite aggregation
    # is equal to the specified num_composite_buckets, then there could still be more
    # composite aggregation buckets that need to be processed and so more queries must
    # be run.
    while (
        len(query_result["aggregations"]["my_buckets"]["buckets"]) == num_composite_buckets
    ):
        process_composite_aggregation_data(query_result)
        query_result = es_cluster.search(index=SK_INDEX_PATTERN, body=query)

    # If the number of buckets in the composite aggregation is less than the specified
    # num_composite_buckets, then there are no more buckets that need to be processed,
    # so we just process the result of the query and are finished once that is done.
    if query_result["aggregations"]["my_buckets"]["buckets"]:
        process_composite_aggregation_data(query_result)

cmd_line_parser = argparse.ArgumentParser()
cmd_line_parser.add_argument("--host")
cmd_line_parser.add_argument("--port")
cmd_line_parser.add_argument("--flow_id")
cmd_line_parser.add_argument("--start_date")
cmd_line_parser.add_argument("--end_date")
arguments = cmd_line_parser.parse_args()

elasticsearch = OpenSearch(hosts = [{'host' : arguments.host, 'port': arguments.port}])

send_query_and_evaluate_result(
    elasticsearch,
    query_avg_response_time,
    DEFAULT_NUM_COMPOSITE_BUCKETS,
    arguments
)
