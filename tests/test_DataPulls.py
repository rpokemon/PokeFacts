#!/usr/bin/env python3

import codecs
import json
from pokefacts import datapulls


class TestDataPulls(object):
    def test_ItemStore(self):
        store = datapulls.ItemStore({'term_property': 'term'})

        with codecs.open('tests/test_data.json', "r", "utf-8") as data_file:
            store.add_items(json.load(data_file))

        assert store.search("charizard").get()['placeholder'] == 1
        assert store.search("charzard").get()['placeholder'] == 1
        assert store.search("charizard mega").get()['placeholder'] == 2
        assert store.search("charzard mega").get()['placeholder'] == 2
        assert store.search("charzard mga").get()['placeholder'] == 2
        assert store.search("venusaur").get()['placeholder'] == 3
        assert store.search("venusaur mega").get()['placeholder'] == 4
        assert store.search("bulbasaur").get()['placeholder'] == 5
        assert store.search("bulbsaur").get('placeholder') == 5

        assert store.search("foobar").is_empty()
