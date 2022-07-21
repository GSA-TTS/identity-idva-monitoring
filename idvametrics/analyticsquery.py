"""
Provides classes representing Elasticsearch queries and functionality for running those queries
against a server and uploading to an index.
"""

import datetime
import hashlib
import typing
import dateutil.parser
import opensearchpy
import analyticsutils

ANALYTICS_TIME_OFFSET = datetime.timedelta(minutes=5)
DEFAULT_NUM_COMPOSITE_BUCKETS = 10


class AnalyticsQuery:
    """
    The base class for creating objects representing an Elasticsearch query.

    Each AnalyticsQuery object is connected to an Elasticsearch server and can upload documents to
    the analytics-* index pattern.
    """

    def __init__(self, query, metric_definition, mappings, args):
        self.elasticsearch = opensearchpy.OpenSearch(
            hosts=[{"host": args.host, "port": args.port}],
            timeout=300,
        )
        self.index_pattern = metric_definition["index_pattern"]
        self.analytics_index_prefix = f"{args.env}-analytics"
        self.query = query
        self.metric_definition = {
            "flow_id": args.flow_id,
            "metric": metric_definition["metric"],
            "metric_keys": metric_definition["metric_keys"],
            "document_keys": metric_definition["document_keys"],
        }
        self.mappings = mappings
        self.date = self.__get_date(args.start_date, args.end_date)

    def __get_date(self, start_date: str, end_date: str):
        """
        Returns an object representing a time range from start_date to end_date.
        """
        if start_date:
            start = analyticsutils.epoch_time(start_date)
        elif start := self.__get_most_recent_timestamp():
            start = analyticsutils.epoch_time(start, ANALYTICS_TIME_OFFSET)
        else:
            start = 0

        if end_date:
            end = analyticsutils.epoch_time(end_date)
        else:
            end = int(datetime.datetime.now().timestamp())

        return {"start_date": start, "end_date": end}

    def run(self) -> None:
        """
        Runs the Elasticsearch query, processes the query result, and uploads the data to the
        analytics index.
        """

    def create_index(self, new_index: str) -> None:
        """
        If we do not have an index titled new_index, we must create it.
        """
        if not self.elasticsearch.indices.exists(new_index):
            self.elasticsearch.indices.create(index=new_index)

    def __get_most_recent_timestamp(self) -> str:
        """
        Retrieves the timestamp of the most recent document in analytics-*, as determined by the
        tsEms field. If the analytics-* index pattern does not exist, or doesn't contain data for
        the tsEms field, return None.
        """
        if not self.elasticsearch.indices.get_alias(f"{self.analytics_index_prefix}-*"):
            # The analytics-* index pattern doesn't exist.
            return None

        # query to obtain the most recent timestamp
        newest_timestamp_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                "flowId": self.metric_definition["flow_id"]
                            },
                        },
                    ],
                },
            },
            "size": 1,
            "sort": [
                {
                    "max_date": {"order": "desc"},
                },
            ],
        }

        res = self.elasticsearch.search(
            index=f"{self.analytics_index_prefix}-*",
            body=newest_timestamp_query,
        )
        try:
            # Attempting to get the time of the most recent timestamp of a document in the analytics
            # index.
            latest_timestamp = res["hits"]["hits"][0]["_source"]["tsEms"]
        except KeyError:
            # Nothing in the analytics index for the given flow_id, so use the current time.
            latest_timestamp = None

        return latest_timestamp


class CompositeAggregationQuery(AnalyticsQuery):
    """
    Class representing an Elasticsearch composite aggregation query.
    """

    def __init__(self, query, metric_definition, mappings, args):
        super().__init__(query, metric_definition, mappings, args)
        self.__format_query()

    def __create_document_id(self, metric_keys) -> str:
        """
        Creates a document identifier, which is determined by the query metric and a metric key.
        """
        document_id = f"{self.metric_definition['metric']}"
        for key in self.metric_definition["metric_keys"]:
            document_id += f"-{metric_keys[key]}"

        return document_id

    def __create_analytics_document(
        self,
        bucket: dict,
        max_date: datetime.datetime,
        min_date: datetime.datetime | None = None,
    ) -> dict:
        """
        Returns an Elasticsearch document which will be uploaded to the dev-analytics-* index
        pattern.
        """
        document = {
            "doc_count": bucket["doc_count"],
            "max_date": max_date,
            "min_date": min_date,
            "companyId": self.mappings["company_id"],
            "flowId": self.metric_definition["flow_id"],
            "flowName": self.mappings["flow_name"],
            "metric": self.metric_definition["metric"],
        }

        # Adding additional query-specific data to the document.
        for document_key in self.metric_definition["document_keys"]:
            document[document_key] = bucket[document_key]["value"]

        for key in self.metric_definition["metric_keys"]:
            document[key] = bucket["key"][key]

        for field in self.metric_definition["top_hit_fields"]:
            document[field] = bucket["top_hits"]["hits"]["hits"][0]["_source"][field]

        if "id" in document:
            try:
                node = [e for e in self.mappings["nodes"] if e["id"] == document["id"]][
                    0
                ]
                document["nodeName"] = node["title"]
                document["nodeDescription"] = node["description"]
            except IndexError:
                document["nodeName"] = None
                document["nodeDescription"] = None

        return document

    def __query(self) -> typing.Any:
        """
        Runs the query against the specified Elasticsearch index.
        """
        return self.elasticsearch.search(index=self.index_pattern, body=self.query)

    def __format_query(self) -> None:
        """
        Ensures the query performs the composite aggregation on a search of a specific flow id for a
        specific time range.
        """
        size = {"size": DEFAULT_NUM_COMPOSITE_BUCKETS}
        analyticsutils.update_nested_key(
            self.query, ["aggs", "composite_buckets", "composite"], size
        )

        # Requiring a max and min aggregation for the timestamp.
        analyticsutils.update_nested_key(
            self.query,
            ["aggs", "composite_buckets", "aggs", "max"],
            {"max": {"field": "tsEms"}},
        )
        analyticsutils.update_nested_key(
            self.query,
            ["aggs", "composite_buckets", "aggs", "min"],
            {"min": {"field": "tsEms"}},
        )

        # Requiring a search on a specified flow_id.
        match_phrase = {
            "match_phrase": {"flowId": {"query": self.metric_definition["flow_id"]}}
        }
        # Defining a time range for the search.
        query_range = {
            "range": {
                "tsEms": {
                    "gte": self.date["start_date"],
                    "lte": self.date["end_date"],
                    "format": "epoch_second",
                }
            }
        }

        try:
            # Adding the match phrase and query range clauses to an existing must clause
            self.query["query"]["bool"]["must"].append(match_phrase)
            self.query["query"]["bool"]["must"].append(query_range)
        except KeyError:
            # The must clause, and potentially query and bool as well, does not exist
            must = {
                "must": [match_phrase, query_range],
            }
            analyticsutils.update_nested_key(self.query, ["query", "bool"], must)

    def __build_bulk_deletes_of_existing_documents(
        self, min_date: str, max_date: str, document_id: str
    ) -> list:
        """
        Build Bulk API delete actions for documents with id document_id to avoid duplication of
        documents within the analytics index.
        """
        bulk_deletes = []

        while min_date < max_date:
            index_date = min_date.strftime("%Y.%m.%d")
            index = f"{self.analytics_index_prefix}-{index_date}"

            if self.elasticsearch.exists(index, document_id):
                bulk_deletes.append(
                    analyticsutils.create_bulk_delete_action(index, document_id)
                )
                break

            index_time_difference = datetime.timedelta(days=1)
            min_date += index_time_difference
        return bulk_deletes

    def __build_bulk_actions_from_query_result(self, buckets: list) -> list:
        """
        From a query result, build a list of bulk API actions containing analytics documents to be
        uploaded to the anlaytics index.
        """

        bulk_actions = []
        for bucket in buckets:
            # Creating the document id, which relies on the metric key defined in
            # bucket["key"]["agg"].
            document_id = hashlib.sha256(
                self.__create_document_id(bucket["key"]).encode()
            ).hexdigest()
            # The document belongs in the analytics index defined by the max_date.
            max_date = dateutil.parser.parse(bucket["max"]["value_as_string"])
            max_date_str = max_date.strftime("%Y.%m.%d")
            index_to_update = f"{self.analytics_index_prefix}-{max_date_str}"

            # Creating bulk actions for deleting the document with id document_id from an analytics
            # index in the date range between min_date and max_date, if the document exists. This
            # ensures we don't have a document with a given document_id saved to multiple indices.
            min_date = dateutil.parser.parse(bucket["min"]["value_as_string"]).date()
            bulk_deletes = self.__build_bulk_deletes_of_existing_documents(
                min_date, max_date.date(), document_id
            )
            bulk_actions.extend(bulk_deletes)

            # If index_to_update has not yet been created, we must do so before sending it any
            # requests.
            self.create_index(index_to_update)

            document = self.__create_analytics_document(bucket, max_date)

            bulk_actions.append(
                analyticsutils.create_bulk_index_action(
                    index_to_update, document_id, document
                )
            )
        return bulk_actions

    def __get_query_results(self) -> list:
        """
        Runs the query and returns all of the composite aggregation results.
        """
        query_buckets = []

        # querying additional composite aggregation buckets until there are no more
        # buckets to process.
        query_result = self.__query()
        buckets = (
            query_result["aggregations"]["composite_buckets"]["buckets"]
            if query_result
            else None
        )
        while query_result and len(buckets) > 0:
            query_buckets.extend(buckets)

            query_composite = self.query["aggs"]["composite_buckets"]["composite"]
            query_after_key = analyticsutils.get_composite_after_key(query_result)
            query_composite["after"] = query_after_key
            query_result = self.__query()
            buckets = (
                query_result["aggregations"]["composite_buckets"]["buckets"]
                if query_result
                else None
            )
        return query_buckets

    def run(self) -> None:
        # will contain all the composite aggregation data
        query_buckets = self.__get_query_results()

        # building the bulk API actions
        bulk_actions = self.__build_bulk_actions_from_query_result(query_buckets)

        # sending the bulk request to Elasticsearch
        print(
            f"Sending {self.metric_definition['metric']} Composite Query Bulk Request "
            f"to {self.analytics_index_prefix}-*"
        )
        opensearchpy.helpers.bulk(self.elasticsearch, bulk_actions)
        print(
            f"Finished sending {self.metric_definition['metric']} Composite Query Bulk Request "
            f"to {self.analytics_index_prefix}-*"
        )


class ScanQuery(AnalyticsQuery):
    """
    Class representing an Elasticsearch scan query.
    """

    def __init__(self, query, metric_definition, mappings, args):
        super().__init__(query, metric_definition, mappings, args)
        self.__format_query()

    def __query(self) -> typing.Any:
        """
        Runs the query against the specified Elasticsearch index.
        """
        return self.elasticsearch.search(
            index=self.index_pattern, body=self.query, scroll="5m"
        )

    def __create_document_id(self, hit):
        """
        Creates a document identifier, which is determined by the query metric and a metric key.
        """
        document_id = f"{self.metric_definition['metric']}"
        for key in self.metric_definition["metric_keys"]:
            try:
                document_id += f"-{hit[key]}"
            except KeyError:
                if key in hit["_source"]:
                    document_id += f"-{hit['_source'][key]}"

        return document_id

    def __format_query(self):
        """
        Ensures the query performs the composite aggregation on a search of a specific flow id for a
        specific time range.
        """
        # Requiring a search on a specified flow_id.
        match_flow_id = {"match_phrase": {"flowId": self.metric_definition["flow_id"]}}

        # defining the date range of the query
        query_range = {
            "range": {
                "tsEms": {
                    "gte": self.date["start_date"],
                    "lte": self.date["end_date"],
                    "format": "epoch_second",
                }
            }
        }

        try:
            # Attempting to add the flow id filter to an existing must clause
            self.query["query"]["bool"]["must"].append(match_flow_id)
            self.query["query"]["bool"]["must"].append(query_range)
        except KeyError:
            # The must clause, and potentially query and bool as well, does not exist
            must = {
                "must": [match_flow_id, query_range],
            }
            analyticsutils.update_nested_key(self.query, ["query", "bool"], must)

    def __create_analytics_document(self, source) -> dict:
        """
        Returns an Elasticsearch document which will be uploaded to the dev-analytics-* index
        pattern.
        """
        document = {
            "companyId": self.mappings["company_id"],
            "doc_count": 1,
            "flowId": self.metric_definition["flow_id"],
            "flowName": self.mappings["flow_name"],
            "max_date": dateutil.parser.parse(source["tsEms"]),
            "metric": self.metric_definition["metric"],
        }

        # Adding query specific fields and data to the document.
        for document_key in self.metric_definition["document_keys"]:
            if isinstance(document_key, dict):
                doc_property = document_key["property"]
                document[doc_property] = source["properties"][doc_property]["value"]
            else:
                document[document_key] = (
                    source[document_key] if document_key in source else ""
                )

        # Adding a nodeName to the document, if required.
        keys = document.keys()
        if "id" in keys:
            node_id = document["id"]
            try:
                node = [e for e in self.mappings["nodes"] if e["id"] == node_id][0]
                document["nodeName"] = node["title"]
            except IndexError:
                document["nodeName"] = (
                    source["connectorId"] if "connectorId" in source else None
                )

        return document

    def __build_bulk_actions_from_query_result(self, query_result: dict) -> list:
        """
        From a query result, build a list of bulk API actions containing analytics documents to be
        uploaded to the anlaytics index.
        """
        scroll_id = query_result["_scroll_id"]
        hits = query_result["hits"]["hits"]
        bulk_actions = []
        while len(hits):
            # Scans return all hits that satisfy the query conditions
            for hit in hits:
                source = hit["_source"]
                # Creating the document id using sha256 hashing
                document_id = self.__create_document_id(hit).encode()
                document_id = hashlib.sha256(document_id).hexdigest()

                document = self.__create_analytics_document(source)

                # Determining the appropriate index to upload the document to and creating that
                # index if it does not exist.
                date = (
                    dateutil.parser.parse(source["tsEms"]).date().strftime("%Y.%m.%d")
                )
                index_to_update = f"{self.analytics_index_prefix}-{date}"
                self.create_index(index_to_update)

                # Creating the bulk index action for the document and adding it to the list of bulk
                # actions that are sent.
                bulk_action = analyticsutils.create_bulk_index_action(
                    index_to_update, document_id, document
                )
                bulk_actions.append(bulk_action)
            query_result = self.elasticsearch.scroll(scroll_id=scroll_id, scroll="1m")
            scroll_id = query_result["_scroll_id"]
            hits = query_result["hits"]["hits"]
        return bulk_actions

    def run(self) -> None:
        query_result = self.__query()

        # building the bulk API actions
        bulk_actions = self.__build_bulk_actions_from_query_result(query_result)

        # sending the bulk request to Elasticsearch
        print(
            f"Sending {self.metric_definition['metric']} Scan Query "
            f"Bulk Request to {self.analytics_index_prefix}-*"
        )
        opensearchpy.helpers.bulk(self.elasticsearch, bulk_actions)
        print(
            f"Finished {self.metric_definition['metric']} Scan Query "
            f"Bulk Request to {self.analytics_index_prefix}-*"
        )
