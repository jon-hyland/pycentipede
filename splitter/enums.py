"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from enum import Enum


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
