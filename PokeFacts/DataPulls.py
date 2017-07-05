#!/usr/bin/env python3

import json
from difflib import SequenceMatcher
from collections import Counter

from PokeFacts.Config import DATA_FILES

# DataPulls.py
# ~~~~~~~~~~~~
# This file is tasked with retrieving data based on the given
# identifier passed from CallResponse

class DataPulls():

    def __init__(self, main):
        self.main = main
        self.reload()

    # reload - should reload the data to pull from
    def reload(self):
        self.store = ItemStore(Config.DATA_CONF)

        for file in Config.DATA_FILES:
            file = self.main.scriptpath + '/' + file.lstrip('/')
            with open(file) as data_file:    
                self.store.addItems(json.load(data_file))


    # getInfo - returns information for the given identifier
    # the result of this function will be used as the elements
    # of the call items passed to Responder
    #
    # Note that identifier:
    #  - has character accents replaced with ASCII variant
    #  - is stripped of all symbols and punctuation
    #  - has multiple whitespace replaced with a single space
    #  - has no leading or trailing whitespace
    def getInfo(self, identifier, match_prefix):
        result = self.store.search(identifier)
        if result.isEmpty():
            return None
        else:
            return result
    

def get(source, property):
    if property in source:
        return source[property]
    return None

def castArray(self, x):
    if type(x) == list:
        return x
    else:
        return [x]

class ItemStore():
    def __init__(self, config):
        self.index      = ItemCluster(None)
        self.config     = config
        self.raw_data   = {}

        if not 'type_property' in self.config:
            self.config['type_property'] = 'type'
            
        if not 'term_property' in self.config:
            self.config['term_property'] = 'terms'
    
    # search(search_term, type=True)
    # type:
    #   search within a specific type(s) (str/list of str or None)
    #   or:
    #    None - only items without a type
    #    True - all types
    def search(self, search_term, type=True):
        return self.index.findCluster(type).findItem(search_terms)

    def addItems(self, data):
        for item in data.items():
            self.addItem(item)

    def addItem(self, item_value):
        item = Item(term = item_value[self.config['term_property']],
                    value = value,
                    # get the items type, use None if the item does not have a type
                    type  = item_value[self.config['type_property']]
                                if self.config['type_property'] in item_value else None )

        type_cluster = self.index.requireCluster(item.type)
        type_cluster.addItem(item)

class ItemCluster():

    def __init__(self, terms, isFalse = True):
        # attributes applying to this cluster
        self.terms      = castArray(terms)
        self.isFalse    = isFalse
        self.items      = {} # real term -> map

        # attributes applying to child clusters
        self.termholder = TermHolder()
        self.clusters   = {} # map of clusters: single term -> cluster
                             # a cluster can have multiple terms, but this dictionary only supports
                             # a single term as a key, so there may be multiple keys pointing to the
                             # same cluster in this dictionary

    def findItem(self, search_term):
        if self.isFalse:
            return Item.newFalseItem()

        real_term = self.termholder.termcorrection(search_term)
        if real_term is None:
            return Item.newFalseItem()
        
        return self.items[real_Term]

    def addItem(self, item):
        self.termholder.addTerm(item.term)
        self.items[item.term] = item

    # ------------------------------------------------------------
    
    def addCluster(self, itemCluster):
        for term in itemCluster.terms:
            self.clusters[term] = itemCluster

    # find a cluster by a list of possible terms
    def findCluster(self, search_terms):
        if self.isFalse:
            return ItemCluster.newFalseCluster()

        for term in castArray(search_terms):
            if term in self.clusters:
                return self.clusters[term]

        return ItemCluster.newFalseCluster()

    # returns the cluster with a specific term
    # creates the cluster if it doesn't exists
    def requireCluster(self, term):
        if self.isFalse:
            return ItemCluster.newFalseCluster()

        if term in self.clusters:
            return self.clusters[term]
        else:
            cluster = ItemCluster(term)
            self.clusters[term] = cluster
            return cluster

    @staticmethod
    def newFalseCluster(self):
        return ItemCluster(None, isFalse=False)

class Item():
    
    def __init__(self, value = None, hasValue=True, type=None, term=None):
        self.value      = value
        self.hasValue   = hasValue
        self.type       = type
        self.term       = term

    def get(self):
        return self.value

    def getOrElse(self, otherwise=None):
        if self.isEmpty():
            return otherwise
        else:
            return self.get()

    def isEmpty(self):
        return not self.hasValue
    
    @staticmethod
    def newFalseItem():
        return Item(hasValue=False)

# helper class used by TermHolder
class TermEntry():

    def __init__(self, term, termwords):
        self.term = term
        self.words = termwords

# helper class used by ItemCluster
class TermHolder():

    def __init__(self):
        self._words = words
        self._terms = terms

        self._wordTermMap = {}
        self._wordCounter = Counter()
        self._PN          = 0

    def addTerm(self, term):
        term = TermEntry(term, term.split())

        self._terms.append(term)
        self._words.extend(term.words)

        for word in term.words:
            self._wordCounter[word] += 1
            self._PN += 1

            if not word in self._wordTermMap:
                self._wordTermMap[word] = []
            self._wordTermMap[word].append(term)


    def termcorrection(self, term):
        if term in self._terms:
            return term

        term = TermEntry(term, [])

        least_common_word = None
        min_word_count = float('inf')

        for word in term.split():
            term.words.append(self.correction(word))

            if not word in self._wordCounter:
                return None

            count = self._wordCounter[word]
            if count < min_word_count:
                min_word_count = count
                least_common_word = word
        
        term.term = " ".join(term.words)

        return TermHolder.closestCandidate(self._wordTermMap[least_common_word], term.term)
    
    def P(self, word, N=self.self._PN):
        "Probability of `word`."
        return self._wordCounter[word] / N

    def correction(self, word):
        "Most probable spelling correction for word."

        if word in self._wordCounter:
            return word

        candidates = self.candidates(word)
        if len(candidates) == 1:
            return candidates.pop()
        
        return max(candidates, key=self.P)
    
    # courtesy http://norvig.com/spell-correct.html
    def candidates(self, word):
        return set(self.known([word]) or self.known(TermHolder.edits1(word)) or self.known(TermHolder.edits2(word)) or [word])
    
    # courtesy http://norvig.com/spell-correct.html
    def known(self, words):
        return set(w for w in words if w in self._words)
    
    # courtesy http://norvig.com/spell-correct.html
    @staticmethod
    def edits1(word):
        "All edits that are one edit away from `word`."
        letters    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)
    
    # courtesy http://norvig.com/spell-correct.html
    @staticmethod
    def edits2(word): 
        "All edits that are two edits away from `word`."
        return (e2 for e1 in TermHolder.edits1(word) for e2 in TermHolder.edits1(e1))

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    @staticmethod
    def closestCandidate(self, candidates, original):
        max_idx = 0
        max_ratio = 0
        for idx, candidate in enumerate(candidates):
            ratio = TermHolder.similar(original, candidate)
            if ratio > max_ratio:
                max_idx = idx
                max_ratio = ratio
        
        return candidates[max_idx]