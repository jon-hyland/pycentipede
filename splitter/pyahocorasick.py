"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

# mypy: ignore-errors

from typing import List
from collections import deque

nil = object()


class TrieNode(object):

    __slots__ = ['char', 'output', 'fail', 'children']
    
    def __init__(self, char):
        self.char = char
        self.output = nil
        self.fail = nil
        self.children = {}
    
    def __repr__(self):
        if self.output is not nil:
            return "<TrieNode '%s' '%s'>" % (self.char, self.output)
        else:
            return "<TrieNode '%s'>" % self.char


class Trie(object):

    def __init__(self):
        self.root = TrieNode('')

    def __get_node(self, word):
        node = self.root
        for c in word:
            try:
                node = node.children[c]
            except KeyError:
                return None
        return node

    def get(self, word, default=nil):
        node = self.__get_node(word)
        output = nil
        if node:
            output = node.output
        if output is nil:
            if default is nil:
                raise KeyError("no key '%s'" % word)
            else:
                return default
        else:
            return output

    def keys(self):
        for key, _ in self.items():
            yield key

    def values(self):
        for _, value in self.items():
            yield value

    def items(self):
        list_ = []

        def aux(node, s):
            s = s + node.char
            if node.output is not nil:
                list_.append((s, node.output))
            for child in node.children.values():
                if child is not node:
                    aux(child, s)

        aux(self.root, '')
        return iter(list_)

    def __len__(self):
        stack = deque()
        stack.append(self.root)
        n = 0
        while stack:
            node = stack.pop()
            if node.output is not nil:
                n += 1

            for child in node.children.values():
                stack.append(child)

        return n

    def add_word(self, word, value):
        if not word:
            return
        node = self.root
        for _, c in enumerate(word):
            try:
                node = node.children[c]
            except KeyError:
                n = TrieNode(c)
                node.children[c] = n
                node = n
        node.output = value

    def clear(self):
        self.root = TrieNode('')

    def exists(self, word):
        node = self.__get_node(word)
        if node:
            return bool(node.output != nil)
        else:
            return False

    def match(self, word):
        return self.__get_node(word) is not None

    def make_automaton(self):
        queue = deque()
        for i in range(256):
            c = chr(i)
            if c in self.root.children:
                node = self.root.children[c]
                node.fail = self.root
                queue.append(node)
            else:
                self.root.children[c] = self.root
        while queue:
            r = queue.popleft()
            for node in r.children.values():
                queue.append(node)
                state = r.fail
                try:
                    while node.char not in state.children:
                        state = state.fail
                    node.fail = state.children.get(node.char, self.root)
                except Exception:  # as ex:
                    # print(ex)
                    pass

    def iter(self, string):
        state = self.root
        for index, c in enumerate(string):
            while c not in state.children:
                state = state.fail
            state = state.children.get(c, self.root)
            tmp = state
            output = []
            while tmp is not nil:
                if tmp.output is not nil:
                    output.append(tmp.output)
                tmp = tmp.fail
            if output:
                yield index, output

    def find_all(self, string: str) -> List[str]:
        words: List[str] = []
        for item_tuple in self.iter(string):
            for word in item_tuple[1]:
                words.append(word)
        return words
