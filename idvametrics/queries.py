"""
Queries for obtaining different dashboard metrics.
"""

# Obtains response time data for each connector.
connector_response_time = {
    "query": {"bool": {"must": [{"exists": {"field": "executionTime"}}]}}
}

# Obtains response time data for a flow.
workflow_response_time = {
    "query": {
        "bool": {
            "filter": [{"match_all": {}}],
        }
    },
    "size": 0,
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
                "sources": [
                    {"interactionId": {"terms": {"field": "interactionId.keyword"}}}
                ]
            },
        },
    },
}

# Obtains success and error data, which will be use to find the pass rate and
# number of successes for connectors.
connector_pass_rate = {
    "query": {
        "bool": {
            "should": [
                {"match_phrase": {"properties.outcomeStatus.value": "success"}},
                {"match_phrase": {"properties.outcomeStatus.value": "error"}},
            ]
        }
    }
}

# Obtains the last timestamp for each interactionId, allowing for the determination
# of where the user dropped off in the flow.
drop_off = {
    "query": {"bool": {}},
    "size": 0,
    "aggs": {
        "composite_buckets": {
            "aggs": {
                "top hits": {
                    "top_hits": {"size": 1, "sort": [{"tsEms": {"order": "desc"}}]}
                }
            },
            "composite": {
                "sources": [
                    {"interactionId": {"terms": {"field": "interactionId.keyword"}}}
                ]
            },
        }
    },
}
