#!/usr/bin/env python3

# DataPulls.py
# ~~~~~~~~~~~~
# This file is tasked with retrieving data based on the given
# identifier passed from CallResponse

# getInfo - returns information for the given identifier
# the result of this function will be used as the elements
# of the call items passed to Responder
#
# Note that identifier:
#  - has character accents replaced with ASCII variant
#  - is stripped of all symbols and punctuation
#  - has multiple whitespace replaced with a single space
#  - has no leading or trailing whitespace
def getInfo(identifier):
    pass