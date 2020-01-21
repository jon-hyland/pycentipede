from enum import Enum
from enum import IntEnum


class VerbosityLevel(IntEnum):
    """Represents three verbosity levels that can be requested."""
    def __str__(self):
        return str(self.name)
    Low = 0
    Medium = 1
    High = 2


class DictionarySource(Enum):
    """Represents the dictionary a term was sourced from.  Sometimes they were present in multiple."""
    Unknown = 0
    GoogleBooks1Gram = 1
    GoogleBooks2Gram = 2
    Manual3Gram = 3
    Supplemental = 4
    Location = 5
    Names = 6
    Scrabble = 7
    Adult = 8


class WordType(Enum):
    """
    Represents the different types a word can be.  Some words might be represented more than once
    in the English language, with different types and different meanings.
    """
    Unknown = 0
    Noun = 1
    Pronoun = 2
    Verb = 3
    Adverb = 4
    Adjective = 5
    Preposition = 6
    Conjunction = 7
    Interjunction = 8
    AdjectiveSatellite = 9


class ServiceStateType(Enum):
    """Represents the state a service can be in."""
    Up = 0
    LoadingData = 1
    Down = 2
