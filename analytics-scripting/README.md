# IDVA Analytics Scripting

Scripts for accessing and preparing IDVA Login data for use in visualization analytics.

## Prerequisites

Must have Python 3 and the [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
installed.

## Running the script

To run the script, enter the `python analytics_script.py <host> <port>` command, where `host` is the
domain of the Elasticsearch server and `port` is the port through which Elasticsearch is accessed.

### Options

#### Flow ID

By default, the script will query data from the Singular Key flow with Flow ID
`t035KrLTyPv3jJao4jzwRrSzyV2gU1oK`. However, the queried flow can be changed with the `--flow_id`
command line option.

#### Date Range

By default, the script relies on a time range defined by 5 minutes before the most recent data in
the `dev-analytics-*` index pattern up to the current time. However, the date range can be modified
with the `--start_date` and `--end_date` command line options.