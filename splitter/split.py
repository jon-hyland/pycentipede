"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from typing import Set, Optional
from splitter.scoring import get_word_value
from splitter.enums import DictionarySource
from splitter.term import Term


class Split:
    """Represents a split section of the original input.  A pass consists of multiple splits.  A split can be
    matched on unmatched.  A matched split is a section that has been matched to a dictionary entry and is
    considered "done" and scored.  An unmatched split will continue to be evaluated, and can be split into
    further splits if found to contain matching words."""

    def __init__(self, text: str, frequency: float = 1E-8, multiplier: float = 1.0, matched: bool = False, sources: Optional[Set] = None):
        """Class constructor."""
        if sources is None:
            sources = set()
        self.__text: str = text
        self.__frequency: float = frequency
        self.__multiplier: float = multiplier
        self.__matched: bool = matched
        self.__sources: Set[DictionarySource] = sources

    @property
    def text(self) -> str:
        """Display version of the split."""
        return self.__text

    @property
    def frequency(self) -> float:
        """Stored frequency value of this split, if matching in a term in the dictionary, or the default frequency."""
        return self.__frequency

    @property
    def multiplier(self) -> float:
        """Stored multiplier value of this split, if matching in a term in the dictionary, or the default multiplier."""
        return self.__multiplier

    @property
    def matched(self) -> bool:
        """True if this split is matched to a term.  If False, either no match or matching hasn't yet occurred."""
        return self.__matched

    @property
    def sources(self) -> Set[DictionarySource]:
        """List of sources, one or more, that the matched term was originally found in."""
        return self.__sources

    def __repr__(self) -> str:
        """Print and debug display."""
        return self.__text if self.__text else ""

    def value(self) -> float:
        """Calculates the value of this split."""
        value = get_word_value(self.__text, self.__frequency, self.__multiplier, self.__sources)
        return value

    def match(self, term: Term) -> None:
        """Mark a split as matched, and set its frequency and multiplier."""
        self.__text = term.full
        self.__frequency = term.frequency
        self.__multiplier = term.multiplier
        sources = set()
        for source in term.sources:
            sources.add(source)
        self.__sources = sources
        self.__matched = True

    def match_without_word(self) -> None:
        """Mark a split as matched, and use default frequency and multiplier."""
        self.__frequency = 1E-8
        self.__multiplier = 1
        if DictionarySource.Unknown not in self.__sources:
            self.__sources.add(DictionarySource.Unknown)
        self.__matched = True

    def clone(self) -> 'Split':
        """Creates a deep copy of the object."""
        sources = set()
        for source in self.__sources:
            sources.add(source)
        split = Split(self.__text, self.__frequency, self.__multiplier, self.__matched, sources)
        return split

    # def to_split(self) -> Split:
    #     """Returns a Split() copy of a Term()."""
    #     sources = set()
    #     for source in self.sources:
    #         sources.add(source)
    #     split = Split(self.full, self.frequency, self.multiplier, True, sources)
    #     return split

    @classmethod
    def from_term(cls, term: Term) -> 'Split':
        """Creates a Split object from a Term."""
        sources = set()
        for source in term.sources:
            sources.add(source)
        split = cls(term.full, term.frequency, term.multiplier, True, sources)
        return split
