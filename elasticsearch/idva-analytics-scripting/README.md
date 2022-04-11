# IDVA Analytics Scripting

Scripts for accessing and preparing IDVA Login data for use in visualization analytics.

## Prerequisites

Must have Python 3 and the [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/en/7.x/)
installed. Note that the Elasticsearch Python Client version should match the version of Elasticsearch.

Additionally, the script requires that Elasticsearch is currently running on port 9432.

## Running the script

To manually run the script, enter `python analytics_script.py` in the command line.

### Date Range

By default, the script relies on a default time range defined by 5 minutes before the most recent data in
the `dev-skevents-analytics-*` index pattern up to the current timestamp. However, the arguments to the
`send_query_and_evaluate_result` function can be modified such that the date range is any desired date
range.