#!/usr/bin/env python3

# Config.py
# ~~~~~~~~
# This file holds the configuration for the bot,
# not including passwords and secrets - those are
# in Secrets.py which is a gitignored file

import re
import sys
import praw

try:
    from PokeFacts import Secrets
except ImportError:
    import Secrets

# APPLICATION AUTH
# ----------------

USERNAME        = "PokeFacts" # case matters!
PASSWORD        = Secrets.PASSWORD
APP_ID          = "9RiijpOogYO53A"
APP_SECRET      = Secrets.APP_SECRET

# APPLICATION META INFO
# ---------------------

DEVELOPERS      = "/u/kwwxis, /u/Haruka-sama"
VERSION         = "1.0.1"
DESCRIPTION     = "Responds to specific text in pokemon subreddits with a response"
USERAGENT       = USERNAME + ":" + DESCRIPTION + " v" + VERSION + " by " + DEVELOPERS
DSN             = "https://103153c555104b6695bc06dc10252c62:ffa3fc21a9ed48aaad63b3109f329fec@sentry.io/1197206"

# OPERATOR CONFIG
# ---------------

OPERATORS = ["kwwxis", "Haruka-sama", "bigslothonmyface", "technophonix1", "D0cR3d", "thirdegree"]

# RESPONDER CONFIG
# ----------------

# list of subreddits the bot is allowed to operate on (case matters!)
SUBREDDITS      = ["pokemon", "PokemonMods"]

# should check comments?
RESPONDER_CHECK_COMMENTS = True

# should check submissions?
RESPONDER_CHECK_SUBMISSIONS = True

# if true, check comments that have been edited on subreddits the bot has 'posts' perms on
RESPONDER_CHECK_EDITED = True

# should check mentions
RESPONDER_CHECK_MENTIONS = True

# should respond to mentions in subreddits outside of SUBREDDITS?
RESPONDER_CHECK_MENTIONS_OTHER_SUBREDDITS = True

# IDENTIFIER CONFIG
# -----------------

IDENTIFIER_TO_LOWER = True
IDENTIFIER_NO_ACCENTS = True
IDENTIFIER_SANITIZE = r"[^A-Za-z0-9 ]"

# DATAPULLS CONFIG
# ----------------

DATA_FILES = ['/data/pokemon.json', '/data/items.json', '/data/moves.json', '/data/abilities.json'] # list of json files for responder to search with
DATA_SYNONYM_FILES = ['/data/synonyms.json']
DATA_CONF = {
    # defines which item property to use for the 'type' field
    # if this property is not set, then all items will have
    # no type (i.e. `None`)
    "type_property": "type",

    # defines which item property to use for the item terms
    "term_property": "term",

    # search a specific type for a given prefix (works for both pair and standalone)
    #  - use `None` to search items that do not have a type
    #  - use a list for searching multiple types
    #  - set to `True` to search over all types including items without types
    # If this property is not set, then all prefixes will search over all types
    "type_for_prefix": {
        "{": True,
        "<": True,
        "!": True,
    }
}
DATA_USE_SYMSPELL = True

# RESPONSE CONFIG
# ---------------

REPLY_TEMPLATE_FILE = "/data/response.txt"
REPLY_SHOULD_STICKY = False # should sticky comment if reply is top level?
REPLY_SHOULD_DISTINGUISH = False # should distinguish comment?

# MATCH STRING
# ------------

# Valid matches (for the current configuration)
#   {POKEMON_NAME}, <POKEMON_NAME>, or !POKEMON_NAME
#   exclamation mark notation does not accept pokemon names containing spaces

# prefixes and suffixes should be same length arrays
# the prefixes and suffixes items of the same index should be pairs
#   e.g.  ['{', '<'] and ['}', '>']
#   not   ['{', '<'] and ['>', '}']

# you can change these
MATCH_PAIR_PREFIXES         = ['{', '<']
MATCH_PAIR_SUFFIXES         = ['}', '>']
MATCH_PAIR_VALUE            = r"[A-Za-zÀ-ÿ0-9\'\-\. ]+"
MATCH_STANDALONE_PREFIXES   = ['!']
MATCH_STANDALONE_VALUE      = r"[A-Za-zÀ-ÿ0-9\'\-]+"

# DO NOT CHANGE ANYTHING BELOW THIS LINE
# --------------------------------------
MATCH_STRING  = ''
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_PAIR_PREFIXES) + ')'
MATCH_STRING += MATCH_PAIR_VALUE
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_PAIR_SUFFIXES) + ')'
MATCH_STRING += '|'
MATCH_STRING += r"(?:^|\s+)"
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_STANDALONE_PREFIXES) + ')'
MATCH_STRING += MATCH_STANDALONE_VALUE
if not type(SUBREDDITS) == list or len(SUBREDDITS) == 0 or "all" in SUBREDDITS:
    print("Invalid Configuration!")
    sys.exit(0)
REDDIT = None
def reddit():
    global REDDIT
    if REDDIT is None:
        REDDIT = praw.Reddit(user_agent      = USERAGENT,
                             client_id       = APP_ID,
                             client_secret   = APP_SECRET,
                             username        = USERNAME,
                             password        = PASSWORD)
    return REDDIT