#!/usr/bin/env python3

import re

from PokeFacts import Config
from PokeFacts import Helpers

helpers = Helpers.Helpers(Config.reddit())

class TestHelpers(object):
    def test_removeAccents(self):
        assert helpers.removeAccents("Flabébé") == "Flabebe"

    def validateIdentifier_getTestData(self):
        test_inputs = [
            "test",
            "Flabébé",
            "ÀÁÂÃÄÅÇÈÉÉËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ",
            "àáâãäåçèéêëìíîïñòóôõöùúûüý",
            "LoReM! @ # $ % ^ & *IpSuM",
            "   lorem    ipsum  ",
            "[lorem] (ispum)",
        ]
        test_data = {}
        for query in test_inputs:
            original = query
            if Config.IDENTIFIER_NO_ACCENTS:
                query = helpers.removeAccents(query)

            if Config.IDENTIFIER_TO_LOWER:
                query = query.lower()

            if type(Config.IDENTIFIER_SANITIZE) == str:
                query = re.sub(Config.IDENTIFIER_SANITIZE, '', query)

            test_data[original] = re.sub(r'\s+', ' ', query).strip()
        return test_data

    def test_validateIdentifier(self):
        test_data = self.validateIdentifier_getTestData()

        amount = len(Config.MATCH_PAIR_PREFIXES)
        for idx, (prefix, suffix) in enumerate(zip(Config.MATCH_PAIR_PREFIXES, Config.MATCH_PAIR_SUFFIXES)):
            mismatch_index  = 0 if idx+1 == amount else idx+1
            mismatch_prefix = Config.MATCH_PAIR_PREFIXES[mismatch_index]
            mismatch_suffix = Config.MATCH_PAIR_SUFFIXES[mismatch_index]

            for input_data, expected_result in test_data.items():
                result = helpers.validateIdentifier(prefix + input_data + suffix)

                assert result == expected_result

                bad_result0 = helpers.validateIdentifier(prefix + input_data + mismatch_suffix)
                bad_result1 = helpers.validateIdentifier(mismatch_prefix + input_data + suffix)

                assert bad_result0 == False
                assert bad_result1 == False

        for idx, prefix in enumerate(Config.MATCH_STANDALONE_PREFIXES):
            for input_data, expected_result in test_data.items():
                result = helpers.validateIdentifier(prefix + input_data)

                assert result == expected_result