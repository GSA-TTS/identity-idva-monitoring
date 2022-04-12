from elasticsearch import Elasticsearch
from elasticsearch import helpers
from datetime import datetime
from dateutil import parser

es_cluster = Elasticsearch(hosts=['http://localhost:9432'])

query = {
	"query": {
		"bool": {
			"must": [
				{
					"match_phrase": {
						"flowId": {}
					}
				},
        {
				  "range": {
      	    "tsEms": {}
      	  }
				}
			],
			"filter": [
				{
					"match_all": {}
				}
			]
		}
	},
	"size": 0,
	"aggs": {
	  "my_buckets": {
	    "aggs": {
	      "min": {
					"min": {
						"field": "tsEms"
					}
				},
				"max": {
					"max": {
						"field": "tsEms"
					}
				},
				"sessionLength": {
  				"bucket_script": {
    				"buckets_path": {
      				"startTime": "min",
      				"endTime": "max"
    				},
    				"script": "params.endTime - params.startTime"
  				}
        }
	    }, 
      "composite": {
        "sources": [
          {
            "agg": {
              "terms": {
                "field": "interactionId.keyword"
              }
            }
          }
        ]
      }
    },
		"hits": {
	    "top_hits": {
	      "_source": ["companyId", "flowId"],
	      "size": 1
	    }
	  }
	}
}

#We want to retrieve all data from dev-skevents with a timestamp at any time or more recent
#than 5 minutes before the timestamp of the most recent data in dev-skevents-analytics-*. This
#ensures that we do not miss any data.
def get_most_recent_timestamp(flowId):
  newest_timestamp_query = {
    "query": {
      "bool": {
        "must": [
          {
            "match_phrase": {
              "flowId": {
                "query": flowId
              }
            }
          }
        ],
        "filter": [
          {
            "match_all": {}
          }
        ]
      }
    },
    "size": 0, 
    "aggs": {
      "types_count": {
        "top_hits": {
          "size": 1,
          "sort": [
            {
              "tsEms": {
                "order": "desc"
              }
            }
          ]
        }
      }
    }
  }

  res = es_cluster.search(index="dev-skevents-analytics-*", body=newest_timestamp_query)
  try:
    return res["aggregations"]["types_count"]["hits"]["hits"][0]["sort"][0]
  except KeyError:
    return None

#If we do not have an index of type prefix for a given date, we must create it
def create_index_if_doesnt_exist(new_index):
  if not es_cluster.indices.exists(new_index):
    es_cluster.indices.create(index=new_index)

#Given the buckets returned from the composite aggregation query, fetch the appropriate data
#from each bucket, create an elasticsearch document using that data, and create the single
#bulk request for that document. Once all documents and corresponding requests have been
#created, send the bulk request to the elasticsearch cluster.
def create_documents_and_send_bulk_request(buckets, source):
  bulk_actions = []
  for bucket in buckets:
    #Should we go through past indices and attempt deletes so the interactionId doesn't appear in multiple indices?
    #The index of the bulk request only applies to the specific index we're attempting to update

    #The document, identified by its interactionId, created from the current bucket belongs in the index defined
    #by the latest date (max_date) of which the interactionId appears. The index is defined by index_to_update
    #and is determined by max_date.
    max_date = parser.parse(bucket["max"]["value_as_string"])
    index_to_update = "dev-skevents-analytics-%s" % max_date.strftime('%Y.%m.%d')

    #If index_to_update has not yet been created, we must do so before sending it any requests.
    create_index_if_doesnt_exist(index_to_update)

    #creating the document, with appropriate data
    document = {
      "doc_count": bucket["doc_count"],
      "min_date": parser.parse(bucket["min"]["value_as_string"]),
      "max_date": max_date,
      "sessionLength": bucket["sessionLength"]["value"],
      "companyId": source["companyId"],
      "flowId": source["flowId"],
      "eventMessage": "Interaction Response Time"
    }

    #creating the single bulk action along with the document, which is
    #stored under "_source"
    bulk_action = {
      "_index": index_to_update,
      "_type": "_doc",
      "_id": bucket["key"]["agg"],
      "_source": document,
      "_op_type": "index"
    }

    bulk_actions.append(bulk_action)
  #sending the bulk request to the Elasticsearch cluster
  helpers.bulk(es_cluster, bulk_actions)

#Obtains necessary data for sending the Bulk API request that updates the
#appropriate indices with the new data. Then prepares for obtaining the next
#num_composite_buckets buckets from the composite aggregation result.
def process_composite_aggregation_data(query_result):
  buckets = query_result["aggregations"]["my_buckets"]["buckets"]
  source = query_result["aggregations"]["hits"]["hits"]["hits"][0]["_source"]
  create_documents_and_send_bulk_request(buckets, source)

  #Composite aggregation queries only return a specified number of buckets,
  #num_composite_buckets in our case. The ordering of the buckets in the
  #composite query is done by the "sources" property. Each time a composite
  #query is run, it will return a key idenitifying the last returned bucket in
  #the composite aggregation ordering. This key is placed into the "after_key"
  #variable in this script. That variable is then used in running subsequent
  #composite aggregation queries, in which we are obtaining additional
  #composite aggregation buckets that we could not get from previous queries.
  #When we add, or update, the "after":{"agg":after_key} structure to the
  #composite aggregation portion of the query, we are telling elasticsearch
  #to return the next num_composite_buckets, as defined by the composite
  #aggregation ordering, from the set of all composite aggregation buckets.
  after_key = query_result["aggregations"]["my_buckets"]["after_key"]["agg"]
  try:
    #Updating the bucket idenifier in the composite["after"] section
    #of the query. This tells elasticsearch to return the next
    #num_composite_buckets in the ordering of the buckets in the
    #composite aggregation results, which appear after the bucket
    #with key after_key.
    query["aggs"]["my_buckets"]["composite"]["after"]["agg"] = after_key
  except KeyError:
    #The first time we run the query, the composite["after"] section
    #does not exist, so we will get a KeyError and must create it.
    query["aggs"]["my_buckets"]["composite"]["after"] = {"agg": after_key}

#specify date range for send_query_and_evaluate_result()? would potentially need the lte in the tsEms range
#Sends the elasticsearch query and calls on a separate function to
#process all query results.
def send_query_and_evaluate_result(es_cluster, query, flowId, num_composite_buckets, dateStart, dateEnd=None):
  #setting the number of buckets we want to view at a time for the composite aggregation
  query["aggs"]["my_buckets"]["composite"]["size"] = num_composite_buckets

  #querying the flow with the specified flowId
  query["query"]["bool"]["must"][0]["match_phrase"]["flowId"] = {"query" : flowId}

  #specifying a date range for the query
  query["query"]["bool"]["must"][1]["range"]["tsEms"] = {
    "gte": dateStart
  }

  if dateEnd is not None:
    query["query"]["bool"]["must"][1]["range"]["tsEms"]["lte"] = dateEnd

  #running the query against dev-skevents in elasticsearch
  query_result = es_cluster.search(index="dev-skevents-*", body=query)

  #len(query_result["aggregations"]["my_buckets"]["buckets"]) is the number of buckets
  #in the composite aggregation. If the number of buckets in the composite aggregation
  #is equal to the specified num_composite_buckets, then there could still be more
  #composite aggregation buckets that need to be processed and so more queries must
  #be run.
  while len(query_result["aggregations"]["my_buckets"]["buckets"]) == num_composite_buckets:
    process_composite_aggregation_data(query_result)
    query_result = es_cluster.search(index="dev-skevents-*", body=query)

  #If the number of buckets in the composite aggregation is less than the specified
  #num_composite_buckets, then there are no more buckets that need to be processed,
  #so we just process the result of the query and are finished once that is done.
  if len(query_result["aggregations"]["my_buckets"]["buckets"]) > 0:
    process_composite_aggregation_data(query_result)

flowId = "t035KrLTyPv3jJao4jzwRrSzyV2gU1oK"

dateStart = get_most_recent_timestamp(flowId)
if dateStart is None:
  dateStart = int(datetime.now().timestamp()) - 300000
else:
  dateStart = dateStart - 300000

send_query_and_evaluate_result(es_cluster, query, flowId, 10, dateStart)
