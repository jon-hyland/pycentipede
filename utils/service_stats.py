import sys
import time
from uuid import UUID, uuid1
from typing import Optional, List, Dict, Tuple
from threading import Lock, Thread, Event
from datetime import datetime, timedelta
from utils import error_handler
from utils.json_writer import JsonWriter


class ServiceStats:
    """Keeps in memory a record of service commands, operations, and tasks.  Rolls this data 
    into presentable summaries.  Commands are valid HTTP commands sent to the service and are 
    tracked by frequency and average duration.  Operations are short-running internal processes 
    that are reported after the fact, to allow tracking by frequency and average duration.
    Tasks are internal processes that are expected to take longer than operations.  Their begin 
    and end times are recorded to allow monitoring of tasks that are still in operation."""

    def __init__(self) -> None:
        """Class constructor."""
        self.__operation_queue: Dict[str, List[OperationStats]] = {}
        self.__operation_rollups: Dict[str, List[OperationRollup]] = {}
        self.__command_queue: Dict[str, List[OperationStats]] = {}
        self.__command_rollups: Dict[str, List[OperationRollup]] = {}
        self.__running_tasks: Dict[UUID, TaskStats] = {}
        self.__completed_tasks: List[TaskStats] = []
        self.__last_swap: datetime = datetime.now()
        self.__queue_lock: Lock = Lock()
        self.__rollup_lock: Lock = Lock()
        self.__task_lock: Lock = Lock()
        self.__signal: Event = Event()
        self.__process_thread: Thread = Thread(target=self.__data_process_thread)
        self.__process_thread.daemon = True
        self.__process_thread.start()

    def log_operation(self, name: str, elapsed_ms: int) -> None:
        """Logs an operation."""
        try:
            if name is None:
                name = ""
            op_stats = OperationStats(name, elapsed_ms, datetime.now(), False)
            with self.__queue_lock:
                if name not in self.__operation_queue:
                    self.__operation_queue[name] = []
                self.__operation_queue[name].append(op_stats)
        except Exception as ex:
            error_handler.log_error(ex)

    def log_command(self, name: str, elapsed_ms: int) -> None:
        """Logs a command."""
        try:
            if name is None:
                name = ""
            cmd_stats = OperationStats(name, elapsed_ms, datetime.now(), False)
            with self.__queue_lock:
                if name not in self.__command_queue:
                    self.__command_queue[name] = []
                self.__command_queue[name].append(cmd_stats)
        except Exception as ex:
            error_handler.log_error(ex)

    def begin_task(self, name: str, total_iterations: int = 0) -> UUID:
        """Starts a long running task and returns its UUID.  Task must be ended on completion."""
        try:
            task_stats = TaskStats(name, total_iterations)
            with self.__task_lock:
                if task_stats.id not in self.__running_tasks:
                    self.__running_tasks[task_stats.id] = task_stats
            return task_stats.id
        except Exception as ex:
            error_handler.log_error(ex)

    def set_task_iterations(self, id_: UUID, total_iterations: int) -> None:
        """Sets the total number of iterations after a task has been started, when the total 
        isn't known until later."""
        try:
            with self.__task_lock:
                if id_ in self.__running_tasks:
                    task_stats = self.__running_tasks[id_]
                    task_stats.set_total_iterations(total_iterations)
        except Exception as ex:
            error_handler.log_error(ex)

    def update_task(self, id_: UUID, completed_iterations: int, is_total: bool) -> None:
        """Updates running task with new number of completed iterations.  This number can be 
        just the number of new iterations since the last update, or the total number of iterations 
        since the task was started."""
        try:
            with self.__task_lock:
                if id_ in self.__running_tasks:
                    task_stats = self.__running_tasks[id_]
                    task_stats.update_task(completed_iterations, is_total)
        except Exception as ex:
            error_handler.log_error(ex)

    def end_task(self, id_: UUID) -> None:
        """Ends the specified task."""
        try:
            with self.__task_lock:
                if id_ in self.__running_tasks:
                    task_stats = self.__running_tasks.pop(id_)
                    task_stats.end_task()
                    self.__completed_tasks.append(task_stats)
                    six_hours_ago = datetime.now() - timedelta(hours=6)
                    while len(self.__completed_tasks) > 0 and self.__completed_tasks[0].end_time < six_hours_ago:
                        self.__completed_tasks.pop(0)
        except Exception as ex:
            error_handler.log_error(ex)

    def __data_process_thread(self) -> None:
        """Internal data processing thread."""
        try:
            self.__signal.set()
            while True:
                try:
                    now = datetime.now()
                    six_hours_ago = now - timedelta(hours=6)
                    if now >= self.__last_swap + timedelta(seconds=6):
                        self.swap_and_rollup(self.__operation_queue, self.__operation_rollups, now, six_hours_ago)
                        self.swap_and_rollup(self.__command_queue, self.__command_rollups, now, six_hours_ago)
                        self.__last_swap = now
                except Exception as ex:
                    error_handler.log_error(ex)
                time.sleep(0.25)
        except Exception as ex:
            error_handler.log_error(ex)

    def swap_and_rollup(self, queue: Dict[str, List['OperationStats']], rollup: Dict[str, List['OperationRollup']], now: datetime, six_hours_ago: datetime) -> None:
        """Rolls up the six second queue into a single object for each unique command or operation.
        Logs each to the AWS CloudWatch service, then appends each to the six hour rolling time window.
        Removes items from the six hour window if they have expired."""
        with self.__queue_lock:
            queue_copy: Dict[str, List['OperationStats']] = queue.copy()
            queue.clear()
        rollup_list = []
        for stats_list in queue_copy.values():
            r = self.__rollup_stats(stats_list, self.__last_swap, now)
            if r is not None:
                rollup_list.append(r)
        with self.__rollup_lock:
            for r in rollup_list:
                if r.name not in rollup:
                    rollup[r.name] = []
                rollup[r.name].append(r)
            for name in rollup.keys():
                while len(rollup[name]) > 0 and rollup[name][0].start_time < six_hours_ago:
                    rollup[name].pop(0)

    @staticmethod
    def __rollup_stats(stats_list: List['OperationStats'], start_time: datetime, end_time: datetime) -> Optional['OperationRollup']:
        """Combines a list of stats into a rollup object."""
        if len(stats_list) == 0:
            return None
        count = 0
        elapsed_sum = 0
        elapsed_min = sys.maxsize
        elapsed_max = -sys.maxsize + 1
        for stats in stats_list:
            count += 1
            elapsed_sum += stats.elapsed_ms
            if stats.elapsed_ms < elapsed_min:
                elapsed_min = stats.elapsed_ms
            if stats.elapsed_ms > elapsed_max:
                elapsed_max = stats.elapsed_ms
        return OperationRollup(stats_list[0].name, count, elapsed_sum, elapsed_min, elapsed_max,
                               stats_list[0].is_ping, start_time, end_time)

    @staticmethod
    def __rollup_rollups(rollups: List['OperationRollup'], end_time: datetime) -> Optional['OperationRollup']:
        """Combines a list of rollup objects into a single rollup object."""
        if len(rollups) == 0:
            return None
        count = 0
        elapsed_sum = 0
        elapsed_min = sys.maxsize
        elapsed_max = -sys.maxsize + 1
        start_time = datetime(year=3000, month=1, day=1)
        for r in rollups:
            count += r.count
            elapsed_sum += r.elapsed_sum
            if r.elapsed_min < elapsed_min:
                elapsed_min = r.elapsed_min
            if r.elapsed_max > elapsed_max:
                elapsed_max = r.elapsed_max
            if r.start_time < start_time:
                start_time = r.start_time
        return OperationRollup(rollups[0].name, count, elapsed_sum, elapsed_min, elapsed_max, rollups[0].is_ping,
                               start_time, end_time)

    def health_check(self) -> None:
        """Called by external maintenance timer."""
        # todo: need to implement this
        pass

    def get_summary(self) -> Tuple[List['OperationRollup'], List['OperationRollup'], List['TaskStats'], List['TaskStats']]:
        """Calculates and returns a summary of each of the stored statistic types."""
        operations: List[OperationRollup] = []
        commands: List[OperationRollup] = []
        running_tasks: List[TaskStats] = []
        completed_tasks: List[TaskStats] = []
        with self.__rollup_lock:
            for name in self.__operation_rollups.keys():
                rollup = self.__rollup_rollups(self.__operation_rollups[name], self.__last_swap)
                if rollup is not None:
                    operations.append(rollup)
            for name in self.__command_rollups.keys():
                rollup = self.__rollup_rollups(self.__command_rollups[name], self.__last_swap)
                if rollup is not None:
                    commands.append(rollup)
        with self.__task_lock:
            now = datetime.now()
            six_hours_ago = now - timedelta(hours=6)
            while len(self.__completed_tasks) > 0 and self.__completed_tasks[0].end_time < six_hours_ago:
                self.__completed_tasks.pop(0)
            for id_ in self.__running_tasks.keys():
                task = self.__running_tasks[id_].clone()
                running_tasks.append(task)
            for task_ in self.__completed_tasks:
                task = task_.clone()
                completed_tasks.append(task)
        operations.sort(key=lambda o: o.name, reverse=False)
        commands.sort(key=lambda o: o.name, reverse=False)
        running_tasks.sort(key=lambda t: t.start_time, reverse=False)
        completed_tasks.sort(key=lambda t: t.start_time, reverse=False)
        return operations, commands, running_tasks, completed_tasks

    def write_runtime_statistics(self, writer: JsonWriter) -> None:
        """Writes runtime statistics."""
        summary = self.get_summary()
        operations = summary[0]
        commands = summary[1]
        running_tasks = summary[2]
        completed_tasks = summary[3]

        writer.write_start_object("serviceStats")
        writer.write_start_array("operations")
        for r in operations:
            writer.write_start_object()
            writer.write_property_value("name", r.name if r.name is not None else "")
            writer.write_property_value("count", r.count)
            writer.write_property_value("elapsedMsAvg", round(r.elapsed_avg, 1))
            writer.write_property_value("elapsedMsMin", r.elapsed_min)
            writer.write_property_value("elapsedMsMax", r.elapsed_max)
            writer.write_property_value("elapsedMsSum", r.elapsed_sum)
            writer.write_property_value("cps", round(r.cps, 2))
            writer.write_end_object()
        writer.write_end_array()
        writer.write_start_array("commands")
        for r in commands:
            writer.write_start_object()
            writer.write_property_value("name", r.name if r.name is not None else "")
            writer.write_property_value("count", r.count)
            writer.write_property_value("elapsedMsAvg", round(r.elapsed_avg, 1))
            writer.write_property_value("elapsedMsMin", r.elapsed_min)
            writer.write_property_value("elapsedMsMax", r.elapsed_max)
            writer.write_property_value("elapsedMsSum", r.elapsed_sum)
            writer.write_property_value("cps", round(r.cps, 2))
            writer.write_end_object()
        writer.write_end_array()
        writer.write_start_array("completedTasks")
        for t in completed_tasks:
            writer.write_start_object()
            writer.write_property_value("name", t.name if t.name is not None else "")
            writer.write_property_value("ips", round(t.iterations_per_second, 1))
            writer.write_property_value("elapsed", str(t.elapsed))  # ?
            writer.write_end_object()
        writer.write_end_array()
        writer.write_start_array("runningTasks")
        for t in running_tasks:
            writer.write_start_object()
            writer.write_property_value("name", t.name if t.name is not None else "")
            writer.write_property_value("ips", round(t.iterations_per_second, 1))
            writer.write_property_value("percentComplete", round(t.percent_complete, 1))
            writer.write_property_value("eta", str(t.eta))  # ?
            writer.write_property_value("elapsed", str(t.elapsed))  # ?
            writer.write_end_object()
        writer.write_end_array()
        writer.write_end_object()


class TaskStats:
    """Stores and calculates statistics for a long running service task, like the daily loading 
    of a large data file."""

    def __init__(self, name: str, total_iterations: int = 0, id_: UUID = None, start_time: datetime = None,
                 end_time: datetime = None, completed_iterations: int = 0, is_complete: bool = False) -> None:
        """Class constructor."""
        self.__id: UUID = id_ if not None else uuid1()
        self.__name: str = name
        self.__start_time: datetime = start_time or datetime.now()
        self.__end_time: datetime = end_time or datetime(1, 1, 1)
        self.__total_iterations: int = total_iterations
        self.__completed_iterations: int = completed_iterations
        self.__is_complete: bool = is_complete

    @property
    def id(self) -> UUID:
        """Returns UUID of task."""
        return self.__id

    @property
    def name(self) -> str:
        """Returns display name if task."""
        return self.__name

    @property
    def start_time(self) -> datetime:
        """Returns start time of task."""
        return self.__start_time

    @property
    def end_time(self) -> datetime:
        """Returns end time of task."""
        return self.__end_time

    @property
    def total_iterations(self) -> int:
        """Returns total iterations of task."""
        return self.__total_iterations

    @property
    def completed_iterations(self) -> int:
        """Returns completed iterations of task."""
        return self.__completed_iterations

    @property
    def is_complete(self) -> bool:
        """Returns true if task complete."""
        return self.__is_complete

    @property
    def elapsed(self) -> timedelta:
        """Returns elapsed time since task started (if running) or total run time if completed."""
        if self.__is_complete:
            td = self.__end_time - self.__start_time
        else:
            td = datetime.now() - self.__start_time
        return td

    @property
    def percent_complete(self) -> float:
        """Returns task completion percentage (0.0 - 100.0)"""
        if self.__total_iterations > 0:
            p = (float(self.__completed_iterations) / float(self.__total_iterations)) * 100.0
        else:
            p = float(0)
        return p

    @property
    def iterations_per_second(self) -> float:
        """Returns average iterations per second."""
        total_seconds = self.elapsed.total_seconds()
        if total_seconds > 0:
            ips = float(self.__completed_iterations / total_seconds)
        else:
            ips = float(0)
        return ips

    @property
    def eta(self) -> timedelta:
        """Returns estimated time until task complete, or zero delta if task complete."""
        total_iterations = float(self.__total_iterations)
        completed_iterations = float(self.__completed_iterations)
        iterations_per_second = self.iterations_per_second
        if total_iterations > 0 and iterations_per_second > 0:
            seconds = ((total_iterations - completed_iterations) / iterations_per_second) * 1.25
            eta = timedelta(seconds=seconds)
        else:
            eta = timedelta(seconds=0)
        return eta

    def set_total_iterations(self, total_iterations: int) -> None:
        """Sets total iterations, since sometimes we don't know the number until after task has begun."""
        self.__total_iterations = total_iterations

    def update_task(self, completed_iterations: int, is_total: bool) -> None:
        """Updates running task with new number of completed iterations.  This number can be just
        the number of new iterations since the last update, or the total number of iterations 
        since the task was started."""
        if is_total:
            self.__completed_iterations = completed_iterations
        else:
            self.__completed_iterations += completed_iterations

    def end_task(self) -> None:
        """Marks task as complete and records end time."""
        self.__end_time = datetime.now()
        self.__completed_iterations = self.__total_iterations
        self.__is_complete = True

    def clone(self) -> 'TaskStats':
        """Returns deep copy of current object."""
        return TaskStats(self.__name, self.__total_iterations, self.__id, self.__start_time, self.__end_time,
                         self.__completed_iterations, self.__is_complete)


class OperationStats:
    """Stores statistics about an internal operation and/or single HTTP command the service has processed."""

    def __init__(self, name: str, elapsed_ms: int, timestamp: datetime, is_ping: bool) -> None:
        """Class constructor."""
        self.__name: str = name
        self.__elapsed_ms: int = elapsed_ms
        self.__timestamp: datetime = timestamp
        self.__is_ping: bool = is_ping

    @property
    def name(self) -> str:
        """Returns operation name."""
        return self.__name

    @property
    def elapsed_ms(self) -> int:
        """Returns operation elapsed time in milliseconds."""
        return self.__elapsed_ms

    @property
    def timestamp(self) -> datetime:
        """Returns time operation was logged (finished, not started)."""
        return self.__timestamp

    @property
    def is_ping(self) -> bool:
        """Returns true if operation is considered a 'ping' or nonessential command."""
        return self.__is_ping


class OperationRollup:
    """Stores rollup statistics for multiple of the same operation, over a short window of time."""

    def __init__(self, name: str, count: int, elapsed_sum: int, elapsed_min: int, elapsed_max: int, is_ping: bool,
                 start_time: datetime, end_time: datetime) -> None:
        """Class constructor."""
        self.__name: str = name
        self.__count: int = count
        self.__elapsed_sum: int = elapsed_sum
        self.__elapsed_min: int = elapsed_min
        self.__elapsed_max: int = elapsed_max
        self.__is_ping: bool = is_ping
        self.__start_time: datetime = start_time
        self.__end_time: datetime = end_time

    @property
    def name(self) -> str:
        """Returns operation name."""
        return self.__name

    @property
    def count(self) -> int:
        """Returns count of of same operations in window."""
        return self.__count

    @property
    def elapsed_sum(self) -> int:
        """Returns sum of elapsed time of same operations in window."""
        return self.__elapsed_sum

    @property
    def elapsed_min(self) -> int:
        """Returns the minimum elapsed time of same operations in window."""
        return self.__elapsed_min

    @property
    def elapsed_max(self) -> int:
        """Returns the maximum elapsed time of same operations in window."""
        return self.__elapsed_max

    @property
    def is_ping(self) -> bool:
        """Returns true if operation is considered a 'ping' or nonessential command."""
        return self.__is_ping

    @property
    def start_time(self) -> datetime:
        """Returns the earliest start time of operations in window."""
        return self.__start_time

    @property
    def end_time(self) -> datetime:
        """Returns the latest end time of same operations in window."""
        return self.__end_time

    @property
    def elapsed_avg(self) -> float:
        """Returns the average elapsed time of same operations in window."""
        return float(self.__elapsed_sum) / float(self.__count)

    @property
    def cps(self) -> float:
        """Returns calculated count-per-second of same operations in window."""
        # test
        # return float(self.__count) / (self.__end_time - self.__start_time).total_seconds()
        elapsed = self.__end_time - self.__start_time
        secs = elapsed.total_seconds()
        cps = float(self.__count) / secs
        return cps

    @property
    def cpm(self) -> float:
        """Returns calculated count-per-minute of same operations in window."""
        # test
        return self.cps / 60.0

    @property
    def midpoint_time(self) -> datetime:
        """Returns calculated midpoint in time of start & end time of same operations in window."""
        # test!
        t0 = datetime(1, 1, 1)
        start_secs = (self.__start_time - t0).total_seconds()
        end_secs = (self.__end_time - t0).total_seconds()
        foo = ((end_secs - start_secs) / 2) + start_secs
        t1 = t0 + timedelta(seconds=foo)
        return t1
