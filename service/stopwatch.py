import time


class Stopwatch:
    """Simple class used to measure time intervals, for performance monitoring, etc."""

    def __init__(self, auto_start: bool = True):
        """Class constructor."""
        self.__start: float = -1.0
        self.__elapsed: float = 0.0
        if auto_start:
            self.start()

    @property
    def elapsed_ms(self) -> int:
        """Returns time elapsed in milliseconds.  Can return value from a running stopwatch."""
        elapsed = self.__elapsed
        if self.__start != -1.0:
            end = time.perf_counter()
            elapsed += (end - self.__start) * 1000.0
        return int(round(elapsed, 0))

    def start(self) -> None:
        """Starts the stopwatch."""
        if self.__start != -1.0:
            raise RuntimeError('Stopwatch already started.')
        self.__start = time.perf_counter()

    def stop(self) -> None:
        """Stops the stopwatch, records time elapsed, and resets the counter."""
        if self.__start == -1.0:
            raise RuntimeError('Stopwatch not started.')
        end = time.perf_counter()
        self.__elapsed += (end - self.__start) * 1000.0
        self.__start = -1.0

    def reset(self) -> None:
        """Resets the counter."""
        self.__start = -1.0
        self.__elapsed = 0.0
