#!/usr/bin/env python3

import re

from pokefacts import config
from pokefacts import helpers

helpers = helpers.Helpers(config.reddit())


class TestHelpers(object):
    def test_remove_accents(self):
        assert helpers.remove_accents("Flabébé") == "Flabebe"

    def validate_identifier_get_test_data(self):
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
            if config.IDENTIFIER_NO_ACCENTS:
                query = helpers.remove_accents(query)

            if config.IDENTIFIER_TO_LOWER:
                query = query.lower()

            if type(config.IDENTIFIER_SANITIZE) == str:
                query = re.sub(config.IDENTIFIER_SANITIZE, '', query)

            test_data[original] = re.sub(r'\s+', ' ', query).strip()
        return test_data

    def test_validate_identifier(self):
        test_data = self.validate_identifier_get_test_data()

        amount = len(config.MATCH_PAIR_PREFIXES)
        for idx, (prefix, suffix) in enumerate(zip(config.MATCH_PAIR_PREFIXES, config.MATCH_PAIR_SUFFIXES)):
            mismatch_index = 0 if idx+1 == amount else idx+1
            mismatch_prefix = config.MATCH_PAIR_PREFIXES[mismatch_index]
            mismatch_suffix = config.MATCH_PAIR_SUFFIXES[mismatch_index]

            for input_data, expected_result in test_data.items():
                result, res_prefix = helpers.validate_identifier(
                    prefix + input_data + suffix)

                assert result == expected_result
                assert res_prefix == prefix

                bad_result0, _ = helpers.validate_identifier(
                    prefix + input_data + mismatch_suffix)
                bad_result1, _ = helpers.validate_identifier(
                    mismatch_prefix + input_data + suffix)

                assert bad_result0 is False
                assert bad_result1 is False

        for idx, prefix in enumerate(config.MATCH_STANDALONE_PREFIXES):
            for input_data, expected_result in test_data.items():
                result, res_prefix = helpers.validate_identifier(
                    prefix + input_data)

                assert result == expected_result
                assert res_prefix == prefix
