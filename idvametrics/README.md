# IDVA Analytics Scripting

Scripts for accessing and preparing IDVA Login data for use in visualization analytics.

## Prerequisites

Must have Python 3 and the [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
installed.

## Running the script

To run the script, enter the `python analytics_script.py --host <host> --port <port> --flow_id <flow_id>` command. where `host` is the
domain of the Elasticsearch server, `port` is the port through which Elasticsearch is accessed, and `flow_id` is the flow identifier
of the flow that will be queried.

### Command Line Options

The `--host`, `--port`, and `--flow_id` are all required for the script to execute without any errors. There are additional command
line options, which are not required, but can be specified, when running the script.

#### Date Range

By default, the script relies on a time range defined by 5 minutes before the most recent data in
the `dev-analytics-*` index pattern up to the current time. However, the date range can be modified
with the `--start_date` and `--end_date` command line options. These options assume, for an
ambiguous integer date format, that the month is provided first followed by day of month and then
year last. If date but no time is provided, the time is assumed to be midnight. The start date
defaults to 5 minutes prior to the current time while the end date defaults to the current time.

## Analytics Conventions

For the purpose of consistency and maintainability, there must exist an established standard
for the placement of analytics connectors within a flow as well as node names and descriptions for
all nodes in a flow.

### Analytics Connectors

A stage in a flow refers to the type of identity verification performed while a step is
an attribute provider's product for the stage. Analytics connectors should be placed at
the end of each step to record the result (success or failure) of the verification at
that step. Each analytics connector has an Outcome Type field which records the attribute
provide and stage of the flow. They should also record the Outcome Status, which is
success or failure as defined above. The analytics connectors should not be used for
another purpose.

### Nodes

Each node in a flow should have a node title and a node description. The node title should be
written in `Title Case` and should provide information on the purpose of the node. The node
description should be written in the format `stage:step` (ex: docv:attributeprovider1),
identifying the location in the flow of the node.
