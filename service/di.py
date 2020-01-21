from service import config
from service.service_state import ServiceState
from service.service_stats import ServiceStats
from service.split_cache import SplitCache
from service.dictionary import Dictionary


"""This is a placeholder for true dependency injection, to be implemented later."""

service_state: ServiceState = ServiceState()
service_stats: ServiceStats = ServiceStats()
split_cache: SplitCache = SplitCache(max_cache_items=config.max_cache_items, cleanup_secs=60.0)
dictionary: Dictionary = Dictionary()
