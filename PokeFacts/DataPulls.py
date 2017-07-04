#!/usr/bin/env python3

import json

# DataPulls.py
# ~~~~~~~~~~~~
# This file is tasked with retrieving data based on the given
# identifier passed from CallResponse

class DataPulls():

    def __init__(self, main):
        self.main = main

    # reload - should reload the data to pull from
    def reload(self):
        self.store = ItemStore('data/pokemon.json', '|~|')

    # getInfo - returns information for the given identifier
    # the result of this function will be used as the elements
    # of the call items passed to Responder
    #
    # Note that identifier:
    #  - has character accents replaced with ASCII variant
    #  - is stripped of all symbols and punctuation
    #  - has multiple whitespace replaced with a single space
    #  - has no leading or trailing whitespace
    def getInfo(self, identifier):
        result = self.store.search(identifier.split())
        if result.isEmpty():
            return None
        else:
            return result.get()
    

class ItemStore():
    def __init__(self, json_file, kwsep=None):
        self.root  = self.__node(None, None,children={})
        self.kwsep = kwsep
        with open(json_file) as data_file:    
            self.raw_data = json.load(data_file)

        self.__build()
    
    def search(self, search_terms):
        if not any(search_terms):
            raise ValueError("search_terms must not be empty")
        print(search_terms)
        if type(search_terms) == str:
            search_terms = [search_terms]

        remove_index = None
        for idx, term in enumerate(search_terms):
            if term in self.root['children']:
                main_node = self.root['children'][term]
                remove_index = idx
                break
        
        if remove_index is None:
            return Item(hasValue = False)
        else:
            search_terms.pop(remove_index)
        print(search_terms)
        if not any(search_terms) and main_node['item'] is not None:
            return main_node['item']
        
        max_count = 0
        idx_max_count = 0
        for idx, child in enumerate(main_node['children']):
            count = 0
            for term in child['terms']:
                if term in search_terms:
                    count += 1
            if count > max_count:
                max_count = count
                idx_max_count = idx
        
        if max_count == 0 and main_node['item'] is not None:
            return main_node['item']
        else:
            main_node = main_node['children'][idx_max_count]
            return main_node['item']


    def __build(self):
        for termstring, value in self.raw_data.items():
            main_node = None
            item = Item(value=value)

            if not self.kwsep is None:
                extra_terms = termstring.split(self.kwsep)
            else:
                extra_terms = [self.termstring]

            # first term is always the primary term
            primary_term = extra_terms.pop(0)

            if any(extra_terms):
                main_node = self.__node(ref=self.root, name=primary_term, value=None, terms=None, children=[])
                self.__node(ref=main_node, value=item, terms=extra_terms, children=[])
            else:
                main_node = self.__node(ref=self.root, name=primary_term, value=item, terms=[], children=[])

    # if 'name' in ref's children already exists, returns that node
    # otherwise creates the new node and returns the node
    def __node(self, ref, name=None, value=None, terms=[], children=[]):
        def nodecontents():
            return {
                'item': value,
                'terms': terms,
                'children': children
            }

        if ref is None:
            return nodecontents()

        if name is None:
            ret = nodecontents()
            ref['children'].append(ret)
            return ret

        if name in ref['children']:
            if not value is None:
                ref['children'][name]['item'] = value
            if any(children):
                ref['children'][name]['children'].extend(children)
            return ref['children'][name]
        
        ret = nodecontents()
        ref['children'][name] = ret
        return ret

class Item():
    
    def __init__(self, value = None, hasValue=True):
        self.value = value
        self.hasValue = hasValue

    def get(self):
        return self.value

    def getOrElse(self, otherwise=None):
        if self.isEmpty():
            return otherwise
        else:
            return self.get()

    def isEmpty(self):
        return not self.hasValue