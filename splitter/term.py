"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from typing import List, Set
from splitter.scoring import get_word_value
from splitter.enums import DictionarySource


class Term:
    """Usually a single word, sometimes a small combination of two+ words that go together.  These terms come from
    many sources, biggest being Google's unigram and bigram analysis of as much historical printed material
    as possible.  Also contains many terms we added manually, especially with boosted values to make technology
    or modern everyday terms more prominent."""

    def __init__(self, text: str, frequency: float, multiplier: float, sources: Set[DictionarySource]) -> None:
        """Class constructor."""
        self.__full: str = text
        if " " in text:
            self.__compressed: str = text.replace(" ", "")
            self.__words: List[str] = text.split(" ")
        else:
            self.__compressed: str = text
            self.__words: List[str] = [text]
        self.__frequency: float = frequency
        self.__multiplier: float = multiplier
        self.__sources: Set[DictionarySource] = sources

    @property
    def full(self) -> str:
        """The original version of the text, including space if term is bi-gram (the end)."""
        return self.__full

    @property
    def compressed(self) -> str:
        """The compressed version of the text, with spaces removed for bi-grams (theend)."""
        return self.__compressed

    @property
    def words(self) -> List[str]:
        """String list containing one or more separate words comprising the term [the, end]."""
        return self.__words

    @property
    def frequency(self) -> float:
        """The frequency of this word, as listed in the source dictionary."""
        return self.__frequency

    @property
    def multiplier(self) -> float:
        """The multiplier of this word, as listed in the source dictionary.  Rarely/never used."""
        return self.__multiplier

    @property
    def sources(self) -> Set[DictionarySource]:
        """Enum list containing one or more original sources the term was found in."""
        return self.__sources

    @property
    def char_count(self) -> int:
        """The length of the term, in compressed format (spaces removed)."""
        return len(self.compressed)

    @property
    def word_count(self) -> int:
        """Number of words in the term."""
        return len(self.words)

    def __repr__(self) -> str:
        """Print and debug display."""
        return self.__full if self.__full else ""

    def value(self) -> float:
        """Calculates the value of this word."""
        value = get_word_value(self.full, self.frequency, self.multiplier, self.sources)
        return value
