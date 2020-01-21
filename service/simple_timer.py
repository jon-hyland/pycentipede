from threading import Thread, Event
from typing import Callable
from datetime import datetime, timedelta


class SimpleTimer:
    """Creates a simple repeating timer.  Runs on a single thread, multiple
    events will not occur at same time."""
    
    def __init__(self, interval_secs: float, target_function: Callable, granularity_sec: float = 0.5):
        self.__thread = Thread(target=self.__run)
        self.__thread.daemon = True
        self.__stop_signal = Event()
        self.__interval_secs = interval_secs
        self.__next_event_time = datetime.now() + timedelta(seconds=interval_secs)
        self.__target_function = target_function
        self.__granularity_secs = granularity_sec

    def __run(self):
        while not self.__stop_signal.wait(self.__granularity_secs):
            if datetime.now() >= self.__next_event_time:
                self.__next_event_time = datetime.now() + timedelta(seconds=self.__interval_secs)
                self.__target_function()

    def start(self):
        self.__thread.start()

    def stop(self):
        self.__stop_signal.set()
