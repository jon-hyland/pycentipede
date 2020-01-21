from typing import List, Dict, Optional, Tuple
from threading import Event
from utils.extensions import has_numbers
from utils.stopwatch import Stopwatch
from utils.service_stats import ServiceStats
from splitter.pyahocorasick import Trie
from splitter.term import Term
from splitter.enums import DictionarySource


class Dictionary:
    """Loads and stores the terms dictionary, supplying the word splitter with data."""

    def __init__(self, service_stats: Optional[ServiceStats] = None) -> None:
        """Class constructor."""
        self.__service_stats: Optional[ServiceStats] = service_stats
        self.__terms: List[Term] = []
        self.__terms_by_compressed: Dict[str, List[Term]] = {}
        self.__special_numbers: List[Term] = []
        self.__word_search: Optional[Trie] = None
        self.__signal: Event = Event()

    def load_data(self, filename: str) -> None:
        """Loads the dictionary file and creates necessary collections."""

        # count file lines (for stats purposes, very fast)
        print(" * Estimating dictionary size..")
        line_count = self.__estimate_dictionary_size(filename)
        
        # load word lists
        print(" * Loading terms from dictionary file..")
        terms_by_full = self.__load_terms(filename, line_count)

        # create other collections
        print(" * Building additional collections..")
        terms_by_compressed, terms, special_numbers = self.__create_collections(terms_by_full)

        # build search index
        print(" * Building aho-corasick index..")
        word_search = self.__build_index(terms)

        # store globals
        self.__terms = terms
        self.__terms_by_compressed = terms_by_compressed
        self.__special_numbers = special_numbers
        self.__word_search = word_search
        
        # set signal
        self.__signal.set()

    def __estimate_dictionary_size(self, filename: str) -> int:
        """Counts number of lines in file.. binary optimized."""
        if (self.__service_stats):
            task_id =self.__service_stats.begin_task("estimate_dictionary_size")
        try:
            def blocks(files, size=65536):
                while True:
                    b = files.read(size)
                    if not b: break
                    yield b
            with open(filename, "r", encoding="utf-8", errors='ignore') as f:
                count = sum(bl.count("\n") for bl in blocks(f))
            return count
        finally:
            if (self.__service_stats):
                self.__service_stats.end_task(task_id)

    def __load_terms(self, filename: str, line_count: int) -> Dict[str, Term]:
        """Loads dictionary terms from prebuilt text file."""
        if (self.__service_stats):
            task_id = self.__service_stats.begin_task("load_dictionary_terms", line_count)
        try:
            terms_by_full: Dict[str, Term] = {}
            count = 0
            with open(filename, "rt") as f:
                for line in f:
                    if (self.__service_stats):
                        count += 1                    
                        if (count % 1000) == 0:
                            self.__service_stats.update_task(task_id, count, True)                
                    if line.startswith("#"):
                        continue
                    split = line.rstrip("\r\n").split("\t")
                    text = split[0]
                    freq = float(split[1])
                    multi = float(split[2])
                    sources_str = split[3].split("|")
                    sources = set()
                    for source_str in sources_str:
                        s = DictionarySource(int(source_str))
                        sources.add(s)
                    t = Term(text, freq, multi, sources)
                    if (DictionarySource.Adult not in t.sources) or (len(t.sources) > 1):
                        terms_by_full[text] = t
            return terms_by_full
        finally:
            if (self.__service_stats):
                self.__service_stats.end_task(task_id)

    def __create_collections(self, terms_by_full: Dict[str, Term]) -> Tuple[Dict[str, List[Term]], List[Term], List[Term]]:
        """Creates the necessary collections."""
        if (self.__service_stats):
            task_id = self.__service_stats.begin_task("create_dictionary_collections", len(terms_by_full))
        try:
            terms_by_compressed: Dict[str, List[Term]] = {}
            terms: List[Term] = []
            special_numbers: List[Term] = []
            count = 0
            for term in terms_by_full.values():
                if (self.__service_stats):
                    count += 1
                    if (count % 1000) == 0:
                        self.__service_stats.update_task(task_id, count, True)
                if term.compressed not in terms_by_compressed.keys():
                    terms_by_compressed[term.compressed]: List[Term] = []
                terms_by_compressed[term.compressed].append(term)
                terms.append(term)
                if (DictionarySource.Supplemental in term.sources) and (has_numbers(term.compressed)):
                    special_numbers.append(term)
            return terms_by_compressed, terms, special_numbers
        finally:
            if (self.__service_stats):
                self.__service_stats.end_task(task_id)

    def __build_index(self, terms: List[Term]) -> Trie:
        """Builds search index."""
        if (self.__service_stats):
            task_id = self.__service_stats.begin_task("create_dictionary_collections", len(terms) * 2)
        try:
            word_search = Trie()
            count = 0
            for term in terms:
                if (self.__service_stats):
                    count += 1
                    if (count % 1000) == 0:
                        self.__service_stats.update_task(task_id, count, True)
                word_search.add_word(term.compressed, term.compressed)
            word_search.make_automaton()
            return word_search
        finally:
            if (self.__service_stats):
                self.__service_stats.end_task(task_id)

    def get_terms(self) -> List[Term]:
        """Returns a pointer to the latest term list."""
        self.__signal.wait()
        return self.__terms

    def get_size(self) -> int:
        """Returns number of terms in the dictionary."""
        self.__signal.wait()
        return len(self.__terms)

    def get_special_numbers(self) -> List[Term]:
        """Returns pointer to list of special numbers."""
        self.__signal.wait()
        return self.__special_numbers

    def find_matching_terms(self, unsplit_input: str, min_chars: int) -> List[Term]:
        """Returns a list of all words contained within the unsplit input.  Optionally excludes words that are too small."""
        self.__signal.wait()
        search_results = self.__word_search.find_all(unsplit_input)
        terms: List[Term] = []
        for r in search_results:
            if r in self.__terms_by_compressed:
                ts = self.__terms_by_compressed[r]
                for term in ts:
                    if term.char_count >= min_chars:
                        terms.append(term)
        return terms

    def find_term(self, compressed_text: str) -> Optional[Term]:
        """Returns the matching Term object if it exists in the dictionary."""
        self.__signal.wait()
        if compressed_text in self.__terms_by_compressed:
            ts = self.__terms_by_compressed[compressed_text]
            best_term = ts[0]
            if len(ts) > 1:
                for t in ts:
                    if t.word_count > best_term.word_count:
                        best_term = t
            return best_term
        return None

    def find_single_word_term(self, compressed_text: str) -> Optional[Term]:
        """Returns the matching Term object if it exists in the dictionary.  Word must be a unigram, or nothing is returned."""
        self.__signal.wait()
        if compressed_text in self.__terms_by_compressed:
            ts = self.__terms_by_compressed[compressed_text]
            if len(ts) > 0:
                highest_freq = 0.0
                highest_term = None
                for t in ts:
                    if (t.word_count == 1) and (t.frequency > highest_freq):
                        highest_freq = t.frequency
                        highest_term = t
                return highest_term
        return None
