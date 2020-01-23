"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from service import config
from utils.service_state import ServiceState
from utils.service_stats import ServiceStats
from splitter.cache import SplitCache
from splitter.dictionary import Dictionary
from splitter.word_splitter import Splitter


"""This is a placeholder for true dependency injection, to be implemented later."""

service_state: ServiceState = ServiceState()
service_stats: ServiceStats = ServiceStats()
split_cache: SplitCache = SplitCache(max_cache_items=config.max_cache_items, cleanup_secs=60.0, service_stats=service_stats)
dictionary: Dictionary = Dictionary(service_stats=service_stats)
word_splitter: Splitter = Splitter(dictionary=dictionary, cache=split_cache, service_stats=service_stats)
