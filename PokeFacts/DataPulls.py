#!/usr/bin/env python3

import re
import sys
import json
import codecs

from difflib import SequenceMatcher
from collections import Counter

try:
    from PokeFacts import Config
    from PokeFacts import Helpers
    from PokeFacts import SymSpell
except ImportError:
    import Config
    import Helpers
    import SymSpell

# DataPulls.py
# ~~~~~~~~~~~~
# This file is tasked with retrieving data based on the given
# identifier passed from CallResponse

class DataPulls():

    def __init__(self, scriptpath=None, store=None, reloadFunc=None):
        self.store = None
        self.reloadFunc = None
        self.scriptpath = None

        if store:
            self.store = store
            self.reloadFunc = reloadFunc
        elif scriptpath:
            self.scriptpath = scriptpath
            self.reload()

    # reload - should reload the data to pull from
    def reload(self):
        if self.reloadFunc:
            self.reloadFunc()
        elif self.scriptpath:
            self.store = ItemStore(Config.DATA_CONF)

            for file in Config.DATA_FILES:
                file = self.scriptpath + '/' + file.lstrip('/')
                with codecs.open(file, "r", "utf-8") as data_file:
                    self.store.addItems(json.load(data_file))

            for file in Config.DATA_SYNONYM_FILES:
                file = self.scriptpath + '/' + file.lstrip('/')
                with codecs.open(file, "r", "utf-8") as data_file:
                    self.store.addSynonyms(json.load(data_file))


    # getInfo - returns information for the given identifier
    # the result of this function will be used as the elements
    # of the call items passed to Responder
    #
    # Note that identifier:
    #  - has character accents replaced with ASCII variant
    #  - is stripped of all symbols and punctuation
    #  - has multiple whitespace replaced with a single space
    #  - has no leading or trailing whitespace
    def getInfo(self, identifier, type=True):
        result = self.store.search(identifier, type=type)
        if result.isEmpty():
            return None
        else:
            return result
    

def get(source, property):
    if property in source:
        return source[property]
    return None

def castArray(x):
    if type(x) == list:
        return x
    else:
        return [x]

class Item():
    def __init__(self, value = None, hasValue=True, type=None, term=None):
        self.value      = value
        self.hasValue   = hasValue
        self.type       = type
        self.term       = term

    def get(self, specific_property=None):
        if specific_property is None:
            return self.value
        elif specific_property in self.value:
            return self.value[specific_property]
        else:
            return None

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

class ItemStore():
    def __init__(self, config):
        self.index      = ItemCluster(None)
        self.config     = config

        if not 'type_property' in self.config:
            self.config['type_property'] = 'type'
            
        if not 'term_property' in self.config:
            self.config['term_property'] = 'terms'
    
    # search(search_term, item_type=True)
    # item_type:
    #   search within a specific type(s) (str/list of str or None)
    #   or:
    #    None - only items without a type
    #    True - all types
    def search(self, search_term, type=True):
        if type == True:
            return ClusterSearchHelper( list(self.index.clusters.values()) ).findItem(search_term)
        elif isinstance(type, list):
            clusters = []
            for t in type:
                if t in self.index.clusters:
                    clusters.append(self.index.clusters[t])
            return ClusterSearchHelper(clusters).findItem(search_term)
        else:
            return self.index.findCluster(type).findItem(search_term)

    def addItems(self, data):
        for item in data:
            self.addItem(item)

    def addItem(self, item_value):
        item_term = item_value[self.config['term_property']]
        
        if Config.IDENTIFIER_NO_ACCENTS:
            item_term = Helpers.Helpers.removeAccents(item_term)

        if Config.IDENTIFIER_TO_LOWER:
            item_term = item_term.lower()
            
        if type(Config.IDENTIFIER_SANITIZE) == str:
            item_term = re.sub(Config.IDENTIFIER_SANITIZE, '', item_term) # remove symbols

        item_term = re.sub(r'\s+', ' ', item_term).strip() # remove extraneous whitespace

        item = Item(term = item_term,
                    value = item_value,
                    # get the items type, use None if the item does not have a type
                    type  = item_value[self.config['type_property']]
                                if self.config['type_property'] in item_value else None )

        type_cluster = self.index.requireCluster(item.type)
        type_cluster.addItem(item)

    def addSynonyms(self, synonyms):
        for old_word, new_word in synonyms.items():
            self.addSynonym(old_word, new_word)

    # only works with single words, not phrases
    def addSynonym(self, old_word, new_word):
        self.index.addSynonym(old_word, new_word)

class ItemCluster():

    def __init__(self, terms, isFalse = False):
        # attributes applying to this cluster
        self.parent     = None
        self.terms      = castArray(terms)
        self.isFalse    = isFalse
        self.items      = {} # real term -> map
        self.synonyms   = {}

        # attributes applying to child clusters
        self.termholder = TermHolder(self)
        self.clusters   = {} # map of clusters: single term -> cluster
                             # a cluster can have multiple terms, but this dictionary only supports
                             # a single term as a key, so there may be multiple keys pointing to the
                             # same cluster in this dictionary

    def findItem(self, search_term):
        return ClusterSearchHelper(self).findItem(search_term)

    def addItem(self, item):
        term_no_spaces = item.term.replace(" ", "")

        if item.term in self.items:
            return

        self.termholder.addTerm(item.term)
        self.termholder.addTerm(term_no_spaces)

        self.items[item.term] = item
        self.items[term_no_spaces] = item

    def addSynonym(self, old_word, new_word):
        self.synonyms[old_word] = new_word

    def findSynonym(self, word):
        '''Find synonym, starts from current cluster and works its way up
        returns None if no synonym found'''
        working_cluster = self
        while working_cluster:
            if word in working_cluster.synonyms:
                return working_cluster.synonyms[word]
            working_cluster = working_cluster.parent
        return None

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
            cluster.parent = self
            self.clusters[term] = cluster
            return cluster

    @staticmethod
    def newFalseCluster():
        return ItemCluster(None, isFalse=False)

class ClusterSearchHelper():

    def __init__(self, clusters):
        self.clusters = []
        for cluster in castArray(clusters):
            if not cluster.isFalse:
                self.clusters.append(cluster)

    def findItem(self, search_term):
        if not any(self.clusters):
            return Item.newFalseItem()

        if len(self.clusters) == 1:
            source_cluster = self.clusters[0]
            real_term, likely = source_cluster.termholder.termcorrection(search_term)
        else:
            real_term, source_cluster = self.findTerm(search_term)

        if real_term is None:
            return Item.newFalseItem()
        
        return source_cluster.items[real_term]

    def findTerm(self, term):
        term = TermEntry(term)

        likely_ratio = 0
        likely_term = None
        likely_cluster = None

        for cluster in self.clusters:
            term_candidate, ratio_candidate = cluster.termholder.termcorrection(term)
            #print('Got', term_candidate, 'at ratio', ratio_candidate)
            # if 100%, no point in checking the rest
            # if above 90%, then it's close enough
            if ratio_candidate >= 0.9:
                return term_candidate, cluster

            # ignore if likelyhood is less than 80%
            if ratio_candidate <= 0.80:
                continue

            if ratio_candidate > likely_ratio:
                likely_ratio    = ratio_candidate
                likely_term     = term_candidate
                likely_cluster  = cluster
        
        return likely_term, likely_cluster

# helper class used by TermHolder
# the purpose of this class is to save a little memory
# as the `_wordTermMap` in TermHolder will have the same
# term as the value of different keys (words). So we have
# all the keys with the same term point to the same object
class TermEntry():

    def __init__(self, term):
        self.term = term
        self.words = term.split()
        self.sortedWords = sorted(self.words)
        self.tokenized = ''.join(self.sortedWords)

termWordDict = SymSpell.SymSpell()

# helper class used by ItemCluster
class TermHolder():

    def __init__(self, parent_cluster):
        self.parent_cluster = parent_cluster

        #self.symspell = SymSpell.SymSpell()

        self._PN = 0 # the total number of words
        self._terms = set() # list of all terms
        self._words = Counter() # word -> number of times the word is used

        self._wordToTermMap = {} # word to term cluster
    
    # approximate size of this TermHolder Object
    def getByteSize(self):
        return sys.getsizeof(self._terms) + sys.getsizeof(self._words) \
                + sys.getsizeof(self._wordToTermMap) + sys.getsizeof(self.symspell.dictionary)

    def addTerm(self, term):
        term = TermEntry(term)

        self._terms.add(term)

        for word in term.words:
            self._words[word] += 1
            self._PN += 1

            if not word in self._wordToTermMap:
                self._wordToTermMap[word] = []
            self._wordToTermMap[word].append(term)

            if Config.DATA_USE_SYMSPELL:
                #self.symspell.create_dictionary_entry(word)
                termWordDict.create_dictionary_entry(word)

    # ------------------------------------------------------------------------------------------
    # TERM CORRECTION

    def termcorrection(self, term):
        if term in self._terms:
            return term, 1.00

        least_common_word = None
        min_word_count = float('inf')

        if not isinstance(term, TermEntry):
            term = TermEntry(term)
        
        # here we're trying to find the least common word
        # in this term in hopes that the cluster using
        # that word has a small amount of term candidates
        new_words1 = []
        new_words2 = []
        for word in term.words:
            old_word = word
            new_word = self.correction(old_word)

            word_similarity = 0 if new_word is None else TermHolder.similar(old_word, new_word)

            if new_word is None or word_similarity <= 0.7:
                new_words1.append(old_word)
                word = old_word
            else:
                new_words1.append(new_word)
                word = new_word
            
            if new_word is not None:
                new_words2.append(new_word)

            if word in self._words:
                count = self._words[word]
                if count < min_word_count:
                    min_word_count = count
                    least_common_word = word

        if least_common_word is None:
            return None, 0.0

        new_token1 = ''.join(sorted(new_words1))
        new_token2 = ''.join(sorted(new_words2))

        max_candidate = None
        max_ratio = 0
        #print(':', new_token1, new_token2, '/', least_common_word, '/', [x.tokenized for x in self._wordToTermMap[least_common_word]])

        # loop over all term candidates in the cluster and compare the similarity
        # to our term. Retrieve the candidate with the most similarity
        for idx, candidate in enumerate(self._wordToTermMap[least_common_word]):
            ratio1 = TermHolder.similar(new_token1, candidate.tokenized)
            if ratio1 > max_ratio:
                max_candidate = candidate
                max_ratio = ratio1

            ratio2 = TermHolder.similar(new_token2, candidate.tokenized)
            if ratio2 > max_ratio:
                max_candidate = candidate
                max_ratio = ratio2
        
        if max_candidate is None:
            return None, 0.00

        return max_candidate.term, max_ratio

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    # ------------------------------------------------------------------------------------------
    # WORD CORRECTION

    def correction(self, word):
        "Most probable spelling correction for word."
        
        if Config.DATA_USE_SYMSPELL:
            #candidates = [ self.symspell.best_word(word) ]
            candidates = [ termWordDict.best_word(word) ]
        else:
            candidates = self.candidates(word)

        synonym = self.parent_cluster.findSynonym(word)
        if synonym is not None:
            candidates.append(synonym)
        else:
            return candidates[0]

        return max(candidates, key=self.P)
    
    def P(self, word):
        "Probability of `word`."
        return self._words[word] / self._PN
    
    # courtesy http://norvig.com/spell-correct.html
    def candidates(self, word):
        edits1 = TermHolder.edits1(word)
        edits2 = TermHolder.edits2(word)
        return set(self.known([word]) or self.known(edits1) or self.known(edits2) or [word])
    
    # courtesy http://norvig.com/spell-correct.html
    def known(self, words):
        return set(w for w in words if w in self._words)
    
    # courtesy http://norvig.com/spell-correct.html
    @staticmethod
    def edits1(word):
        "All edits that are one edit away from `word`."
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in ALPHABET]
        inserts    = [L + c + R               for L, R in splits for c in ALPHABET]
        return set(deletes + transposes + replaces + inserts)
    
    # courtesy http://norvig.com/spell-correct.html
    @staticmethod
    def edits2(word): 
        "All edits that are two edits away from `word`."
        return (e2 for e1 in TermHolder.edits1(word) for e2 in TermHolder.edits1(e1))

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'