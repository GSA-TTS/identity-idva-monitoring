"""
This file is for analytics scripting, querying data from the skevents-* and eventsoutcome-*
index patterns and placing the result in the analytics-* index pattern for further
visualizations.
"""

import analyticsconstants
from analytics_query import CompositeAggregationQuery, ScanQuery
import queries


def main() -> None:
    """
    The main method for running the script.
    """

    connector_pass_rate = ScanQuery(
        queries.connector_pass_rate,
        analyticsconstants.EVENTS_INDEX_PATTERN,
        analyticsconstants.METRIC_DEFINITIONS["connector_pass_rate"],
    )
    connector_pass_rate.send_query_and_evaluate_results()

    connector_response_time = ScanQuery(
        queries.connector_response_time,
        analyticsconstants.SK_INDEX_PATTERN,
        analyticsconstants.METRIC_DEFINITIONS["connector_response_time"],
    )
    connector_response_time.send_query_and_evaluate_results()

    workflow_response_time = CompositeAggregationQuery(
        queries.workflow_response_time,
        analyticsconstants.SK_INDEX_PATTERN,
        analyticsconstants.METRIC_DEFINITIONS["interaction_response_time"],
    )
    workflow_response_time.send_query_and_evaluate_results()


if __name__ == "__main__":
    main()
