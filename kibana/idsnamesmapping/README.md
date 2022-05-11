# Flow and Node Id Mapping

Script for mapping idva flow ids to flow names and node ids to node titles.

## Prerequisites

Must have Python 3 and the [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
installed.

## Running the script

To run the script, enter the `python analytics_script.py --host <host> --port <port> --flow_ids <flow_id> --email <email> --password <password> --loginurl <loginurl> --flowsurl <flowsurl>` command, where `host` is the
domain of the Elasticsearch server and `port` is the port through which Elasticsearch is accessed. `flow_ids` is a comma-separated list
of flow ids, or "all" if performing the mapping on all flows. `email` and `password` provide the necessary authentication to the domain
defined by `loginurl`, which will provide an access token for obtaining data from the domain defined by `flowsurl`.

### Command Line Options

The `--host` and `--port` are required for the script to execute without any errors. By default, `flow_ids` will have a value of "all". The
`email`, `password`, `loginurl`, and `flowsurl` options all must be provided or the script will exit with an error.
