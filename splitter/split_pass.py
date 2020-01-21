from typing import Optional, List
from utils.extensions import substring
from splitter.scoring import get_word_value
from splitter.split import Split
from splitter.term import Term


class Pass:
    """One possible split answer, containing one or more splits (slices of original text).  There will be dozens to
    thousands of passes generated per split operation.  Each pass is scored, and the highest is considered winner."""

    def __init__(self, input_: str = "", splits: List[Split] = None, display_text: str = None,
                 unique_string: str = None) -> None:
        """Class constructor."""
        self.__input: str = input_
        if splits is None:
            s = input_.lower().strip()
            self.__splits: List[Split] = [Split(s)]
        else:
            self.__splits: List[Split] = splits
        self.__display_text: str = display_text
        self.__unique_string: str = unique_string
        self.__value: Optional[float] = None
        self.__score: Optional[float] = None

    @property
    def input(self) -> str:
        """Original input used to generate pass."""
        return self.__input

    @property
    def splits(self) -> List[Split]:
        """List of Split objects that make up the pass."""
        return self.__splits

    def __repr__(self) -> str:
        """Print and debug display."""
        return self.display_text()

    def display_text(self) -> str:
        """Prints all splits, separated by a space, as a single string."""
        if self.__display_text is None:
            self.__display_text = self.__generate_display_text()
        return self.__display_text

    def __generate_display_text(self) -> str:
        """Regenerates value."""
        text = ""
        for s in self.__splits:
            if len(text) != 0:
                text += " "
            text += s.text
        return text

    def unique_string(self) -> str:
        """A string representation of the splits in this pass and their state.  Used to determine if there are duplicate passes, and not include them."""
        if self.__unique_string is None:
            self.__unique_string = self.__generate_unique_string()
        return self.__unique_string

    def __generate_unique_string(self) -> str:
        """Generates a unique string."""
        unique = ""
        for s in self.__splits:
            if len(unique) != 0:
                unique += "|"
            unique += s.text + ":" + ("1" if s.matched else "0")
        return unique

    def is_done(self) -> bool:
        """Returns true if all splits are marked as matched."""
        for s in self.__splits:
            if not s.matched:
                return False
        return True

    def average_word_value(self) -> float:
        """Returns the average word value."""
        total_value = 0.0
        for s in self.__splits:
            total_value += get_word_value(s.text, s.frequency, s.multiplier, s.sources)
        avg = total_value / float(len(self.__splits))
        return avg

    def unmatched_split_count(self) -> int:
        """Count and return number of unmatched splits."""
        count = 0
        for s in self.__splits:
            if not s.matched:
                count += 1
        return count

    def match_ratio(self) -> float:
        """Returns the ratio of matched characters (in all splits combined) from 0 to 1."""
        total_chars = 0.0
        matched_chars = 0.0
        for s in self.__splits:
            total_chars += float(len(s.text))
            if s.matched:
                matched_chars += float(len(s.text))
        ratio = matched_chars / total_chars
        return ratio

    def total_splits(self) -> int:
        """Returns the total number of words (counts each word group as a single unit)."""
        return len(self.__splits)

    def score(self) -> float:
        """Calculates (and caches for speed) the overall score for this pass."""
        if self.__score is None:
            if self.__value is None:
                self.__value = self.average_word_value()
            score = self.__value
            unused_words = self.unmatched_split_count()
            if unused_words == 0:
                score *= 2
            else:
                score *= self.match_ratio()
            self.__score = score
        return self.__score

    def split(self, split_index: int, start_index: int, length: int, term: Term) -> None:
        """Splits the specified segment into two pieces, marking the matching segment as used.
        If the entire specified segment is identified no split occurs, the segment is just marked as matched."""
        source_split = self.__splits[split_index]
        if len(source_split.text) == length:
            source_split.match(term)
        else:
            # split1: Optional[Split] = None
            # split2: Optional[Split] = None
            split3: Optional[Split] = None
            if start_index == 0:
                split1 = Split.from_term(term)
                split2 = Split(substring(source_split.text, length))
            elif (start_index + length) < len(source_split.text):
                split1 = Split(substring(source_split.text, 0, start_index))
                split2 = Split.from_term(term)
                split3 = Split(substring(source_split.text, (start_index + length)))
            else:
                split1 = Split(substring(source_split.text, 0, start_index))
                split2 = Split.from_term(term)
            self.__splits.pop(split_index)
            if split3 is not None:
                self.__splits.insert(split_index, split3)
            if split2 is not None:
                self.__splits.insert(split_index, split2)
            if split1 is not None:
                self.__splits.insert(split_index, split1)
        self.generate_stored_values()

    def generate_stored_values(self) -> None:
        """Regenerates the stored and cached values.  Values are cached for performance, but must be regenerated anytime the contents of a pass change."""
        self.__display_text = self.__generate_display_text()
        self.__unique_string = self.__generate_unique_string()

    def clone(self) -> 'Pass':
        """Creates a copy of the object."""
        splits: List[Split] = []
        for split in self.__splits:
            s = split.clone()
            splits.append(s)
        p = Pass(self.__input, splits, self.__display_text, self.__unique_string)
        return p
