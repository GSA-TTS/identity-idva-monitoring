"""
Constants for use in analytics scripting.
"""

from datetime import timedelta

ANALYTICS_INDEX_PATTERN = "dev-analytics-*"
EVENTS_INDEX_PATTERN = "dev-eventsoutcome-*"
SK_INDEX_PATTERN = "dev-skevents-*"
DEFAULT_NUM_COMPOSITE_BUCKETS = 100
FIVE_MINS = timedelta(minutes=5)
ONE_DAY = timedelta(days=1)
METRIC_DEFINITIONS = {
    "connector_pass_rate": {
        "index_pattern": EVENTS_INDEX_PATTERN,
        "metric": "connector_pass_rate",
        "metric_keys": ["flowId", "interactionId", "id", "tsEms"],
        "document_keys": ["id", "connectionId", {"property": "outcomeStatus"}],
    },
    "connector_response_time": {
        "index_pattern": SK_INDEX_PATTERN,
        "metric": "connector_response_time",
        "metric_keys": ["interactionId", "id", "tsEms"],
        "document_keys": ["executionTime"],
    },
    "interaction_response_time": {
        "index_pattern": SK_INDEX_PATTERN,
        "metric": "interaction_response_time",
        "metric_keys": ["interactionId"],
        "document_keys": ["sessionLength"],
    },
}
