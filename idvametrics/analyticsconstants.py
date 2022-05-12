"""
Constants for use in analytics scripting.
"""

from datetime import timedelta

ANALYTICS_INDEX_PATTERN = "dev-analytics"
EVENTS_INDEX_PATTERN = "dev-eventsoutcome-*"
SK_INDEX_PATTERN = "dev-skevents-*"
DEFAULT_NUM_COMPOSITE_BUCKETS = 100
FIVE_MINS = timedelta(minutes=5)
ONE_DAY = timedelta(days=1)
