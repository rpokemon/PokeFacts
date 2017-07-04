#!/usr/bin/env python3

from PokeFacts import DataPulls

class TestDataPulls(object):
    def test_ItemStore(self):
        store = DataPulls.ItemStore('tests/test_data.json', '|~|')

        assert store.search(["bulbasaur"]).get()['placeholder'] == 1
        assert store.search(["ivysaur"]).get()['placeholder'] == 2
        assert store.search(["venusaur"]).get()['placeholder'] == 3
        assert store.search(["venusaur", "foobar"]).get()['placeholder'] == 3
        assert store.search(["foobar", "venusaur"]).get()['placeholder'] == 3
        assert store.search(["venusaur", "mega"]).get()['placeholder'] == 4
        assert store.search(["venusaur", "m"]).get()['placeholder'] == 4
        assert store.search(["venusaur", "m", "foobar"]).get()['placeholder'] == 4
        
        assert store.search(["foobar"]).isEmpty() == True