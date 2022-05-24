"""
This file is for analytics scripting, querying data from the skevents-* and eventsoutcome-*
index patterns and placing the result in the analytics-* index pattern for further
visualizations.
"""

import argparse
import analyticsconstants
from analytics_query import CompositeAggregationQuery, ScanQuery
import analyticsutils
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


def main() -> None:
    """
    The main method for running the script.
    """
    arguments = get_command_line_arguments()

    mappings = analyticsutils.get_mappings(
        arguments.flow_id,
        arguments.username,
        arguments.password,
        arguments.base_url,
    )

    connector_pass_rate = ScanQuery(
        queries.connector_pass_rate,
        analyticsconstants.METRIC_DEFINITIONS["connector_pass_rate"],
        mappings,
        arguments,
    )
    connector_pass_rate.send_query_and_evaluate_results()

    connector_response_time = ScanQuery(
        queries.connector_response_time,
        analyticsconstants.METRIC_DEFINITIONS["connector_response_time"],
        mappings,
        arguments,
    )
    connector_response_time.send_query_and_evaluate_results()

    workflow_response_time = CompositeAggregationQuery(
        queries.workflow_response_time,
        analyticsconstants.METRIC_DEFINITIONS["interaction_response_time"],
        mappings,
        arguments,
    )
    workflow_response_time.send_query_and_evaluate_results()


if __name__ == "__main__":
    main()
