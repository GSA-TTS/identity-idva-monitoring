# Flow and Node Id Mapping

Script for mapping idva flow ids to flow names and node ids to node titles.

## Prerequisites

Must have Python 3 and the [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
installed.

## Running the script

To run the script, enter the `python analytics_script.py --host <host> --port <port> --flow_id <flow_id>` command. where `host` is the
domain of the Elasticsearch server and `port` is the port through which Elasticsearch is accessed. `flow_id` is a comma-separated list
of flow ids, or "all" if performing the mapping on all flows.

### Command Line Options

The `--host` and `--port` are required for the script to execute without any errors. By default, `flow_id` will have a value of "all".
