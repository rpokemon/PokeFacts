#!/usr/bin/env python3

import codecs, json
from PokeFacts import RedditBot
from PokeFacts import DataPulls

def getDataPullsObject():
    store = DataPulls.ItemStore({'term_property': 'term'})

    with codecs.open('tests/test_data.json', "r", "utf-8") as data_file:
        store.addItems(json.load(data_file))

    return DataPulls.DataPulls(store=store)

def test_GetCalls():
    main = RedditBot.CallResponse(reddit=False, data=getDataPullsObject())

    calls = main.get_calls("{charizard} {charzard} { charizard }")
    assert len(calls) == 1
    assert calls[0].term == 'charizard'