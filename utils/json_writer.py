"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

class JsonWriter:
    """Simple JSON text writer, used for manual creation of a JSON string."""

    def __init__(self) -> None:
        """Class constructor."""
        self.__json = ""
        self.__level = 0
        self.__last_end_level = -1

    def __repr__(self):
        """Print and debug display."""
        return self.__json

    def write_start_object(self, name=None):
        """Writes object start, with optional name."""
        if name is None:
            self.__json += self.__comma__() + "\n" + self.__indent__() + "{"
            self.__in_level__()
        else:
            self.__json += self.__comma__() + "\n" + self.__indent__() + "\"" + name + "\": {"
            self.__in_level__()

    def write_end_object(self):
        """Writes object end."""
        self.__out_level__()
        self.__last_end_level = self.__level
        self.__json += "\n" + self.__indent__() + "}"

    def write_start_array(self, name=None):
        """Writes array start, with optional name."""
        if name is None:
            self.__json += self.__comma__() + "\n" + self.__indent__() + "["
            self.__in_level__()
        else:
            self.__json += self.__comma__() + "\n" + self.__indent__() + "\"" + name + "\": ["
            self.__in_level__()

    def write_end_array(self):
        """Writes array end."""
        self.__out_level__()
        self.__last_end_level = self.__level
        self.__json += "\n" + self.__indent__() + "]"

    def write_property_value(self, name, value):
        """Writes a simple property object with a name and value."""
        self.__json += self.__comma__() + "\n" + self.__indent__() + "\"" + name + "\": " + self.__write_value(value)
        self.__last_end_level = self.__level

    def write_value(self, value):
        """Writes a value at current location.  Performs limited type checking (adds quotes around strings),
        might need more logic for advanced data-types."""
        self.__json += self.__write_value(value)

    def to_string(self):
        """Returns the rendered JSON string."""
        return self.__json.strip()

    def __indent__(self):
        """Returns correct number of intent spaces."""
        ind = ""
        for _ in range(self.__level):
            ind += "  "
        return ind

    def __comma__(self):
        """Writes a comma if one is needed."""
        if self.__level == self.__last_end_level:
            return ","
        return ""

    def __in_level__(self):
        """Increments level by one."""
        self.__level += 1

    def __out_level__(self):
        """Decrements level by one."""
        self.__level -= 1

    @staticmethod
    def __write_value(value):
        """Writes a single value, with correct output for different value types."""
        val = ""
        if isinstance(value, str):
            val += "\""
        val += str(value)
        if isinstance(value, str):
            val += "\""
        return val
