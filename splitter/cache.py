from typing import Optional, Dict
from threading import Lock
from utils.simple_timer import SimpleTimer
from utils.stopwatch import Stopwatch
from utils.json_writer import JsonWriter
from utils.service_stats import ServiceStats
from splitter.split_result import SplitResult


class SplitCache:
    """Stores split results in memory for quick access, periodically purging entries with fewest hits."""

    def __init__(self, max_cache_items: int, cleanup_secs: float = 60.0, service_stats: Optional[ServiceStats] = None) -> None:
        """Class constructor."""        
        self.__max_cache_items: int = max_cache_items
        self.__service_stats: Optional[ServiceStats] = service_stats
        self.__lock: Lock = Lock()
        self.__cache: Dict[str, SplitCache.CacheItem] = {}
        self.__sets: int = 0
        self.__hits: int = 0
        self.__misses: int = 0
        self.__timer: SimpleTimer = SimpleTimer(cleanup_secs, self.__timer_callback)
        self.__timer.start()

    @property
    def count(self) -> int:
        with self.__lock:
            return len(self.__cache)
          
    def set_item(self, input_: str, result: SplitResult) -> None:
        """Stores a result in the cache, indexed by input string."""
        with self.__lock: 
            self.__sets += 1
            if input_ in self.__cache:
                self.__cache[input_].increment_hits()
            else:
                self.__cache[input_] = SplitCache.CacheItem(input_, result)
    
    def get_item(self, input_: str) -> Optional[SplitResult]:
        """Fetches specified result from the cache, or returns None if doesn't exist."""
        with self.__lock:
            if input_ in self.__cache:
                self.__hits += 1
                self.__cache[input_].increment_hits()
                return self.__cache.get(input_).result
            else:
                self.__misses += 1
                return None

    def __timer_callback(self) -> None:
        """Fired by timer, removes cached items with lowest hit counts."""
        with self.__lock:
            if len(self.__cache) > self.__max_cache_items:
                if (self.__service_stats):
                    task_id = self.__service_stats.begin_task(name="", total_iterations=int(len(self.__cache) - self.__max_cache_items * 0.9))
                try:
                    values = list(self.__cache.values())
                    values.sort(key=lambda x: x.hits, reverse=False)
                    while len(values) > self.__max_cache_items * 0.9:
                        input_ = values.pop(0).input
                        if input_ in self.__cache:
                            self.__cache.pop(input_)                    
                finally:
                    if (self.__service_stats):
                        self.__service_stats.end_task(task_id)
    
    def write_runtime_statistics(self, writer: JsonWriter) -> None:
        with self.__lock:
            count = len(self.__cache)
            sets = self.__sets
            hits = self.__hits
            misses = self.__misses
            if (self.__hits + self.__misses) != 0:
                percent = round((float(self.__hits) / float(self.__hits + self.__misses)) * 100.0, 1)
            else:
                percent = 0.0
        writer.write_start_object("splitCache")
        writer.write_property_value("itemCount", count)
        writer.write_property_value("sets", sets)
        writer.write_property_value("hits", hits)
        writer.write_property_value("misses", misses)
        writer.write_property_value("efficiencyPercent", percent)
        writer.write_end_object()
    
    class CacheItem:
        """Internal class to store result, along with hit count."""
        
        def __init__(self, input_: str, result: SplitResult) -> None:
            """Class constructor."""
            self.__input: str = input_
            self.__hits: int = 1
            self.__result: SplitResult = result
        
        @property
        def input(self) -> str:
            """Returns original input."""
            return self.__input

        @property
        def hits(self) -> int:
            """Returns hit count."""
            return self.__hits

        @property
        def result(self) -> SplitResult:
            """Returns stored result."""
            return self.__result
        
        def increment_hits(self) -> None:
            """Increments hit count by one."""
            self.__hits += 1
