#!/usr/bin/env python3

import codecs
import json
from pokefacts import redditbot
from pokefacts import datapulls


def getDataPullsObject():
    store = datapulls.ItemStore({'term_property': 'term'})

    with codecs.open('tests/test_data.json', "r", "utf-8") as data_file:
        store.add_items(json.load(data_file))

    return datapulls.DataPulls(store=store)


def test_GetCalls():
    main = redditbot.CallResponse(reddit=False, data=getDataPullsObject())

    calls = main.get_calls("{charizard} {charzard} { charizard }")
    assert len(calls) == 1
    assert calls[0].term == 'charizard'
