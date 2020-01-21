from threading import Lock
from service.enums import ServiceStateType
from service.json_writer import JsonWriter


class ServiceState:
    """Tracks and reports state of running service."""

    def __init__(self) -> None:
        """Class constructor."""
        self.__lock: Lock = Lock()
        self.__state: ServiceStateType = ServiceStateType.Down
    
    @property
    def state(self) -> ServiceStateType:
        """Returns service state."""
        with self.__lock:
            return self.__state

    def set_up_state(self) -> None:
        """Sets the service state to Up."""
        with self.__lock:
            self.__state = ServiceStateType.Up

    def set_loading_data_state(self) -> None:
        """Sets the service state to LoadingData."""
        with self.__lock:
            self.__state = ServiceStateType.LoadingData

    def set_down_state(self) -> None:
        """Sets the service state to Down."""
        with self.__lock:
            self.__state = ServiceStateType.Down
    
    def write_runtime_statistics(self, writer: JsonWriter) -> None:
        """Writes runtime statistics."""
        state_ = self.state
        writer.write_start_object("serviceState")
        writer.write_property_value("state", state_.name)
        writer.write_end_object()
