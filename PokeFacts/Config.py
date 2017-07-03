#!python3

# Config.py
# ~~~~~~~~
# This file holds the configuration for the bot,
# not including passwords and secrets - those are
# in Secrets.py which is a gitignored file

import re
import sys
import Secrets

# APPLICATION AUTH
# ----------------

USERNAME        = "PokeFacts" # case matters!
PASSWORD        = Secrets.PASSWORD
APP_ID          = "9RiijpOogYO53A"
APP_SECRET      = Secrets.APP_SECRET

# APPLICATION META INFO
# ---------------------

DEVELOPERS      = "/u/kwwxis"
VERSION         = "1.0.0"
DESCRIPTION     = "Responds to specific text in pokemon subreddits with a response"
USERAGENT       = USERNAME + ":" + DESCRIPTION + " v" + VERSION + " by " + DEVELOPERS

# RESPONDER CONFIG
# ----------------

# list of subreddits the bot is allowed to operate on (case matters!)
SUBREDDITS      = ["pokemon"]

# should check comments?
RESPONDER_CHECK_COMMENTS = True

# should check submissions?
RESPONDER_CHECK_SUBMISSIONS = True

# if true, check comments that have been edited on subreddits the bot has 'posts' perms on
RESPONDER_CHECK_EDITED = True

# should check mentions
RESPONDER_CHECK_MENTIONS = True

# should respond to mentions in subreddits outside of SUBREDDITS?
RESPONDER_CHECK_MENTIONS_OTHER_SUBREDDITS = False

# IDENTIFIER CONFIG
# -----------------

IDENTIFIER_TO_LOWER = True
IDENTIFIER_NO_ACCENTS = True
IDENTIFIER_SANITIZE = r"[^A-Za-z0-9 ]"

# RESPONSE CONFIG
# ---------------

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
MATCH_PAIR_VALUE            = r"[A-Za-z0-9\'\-\. ]+"
MATCH_STANDALONE_PREFIXES   = ['!']
MATCH_STANDALONE_VALUE      = r"[A-Za-z0-9\'\-]+"

# DO NOT CHANGE ANYTHING BELOW THIS LINE
# --------------------------------------
MATCH_STRING  = ''
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_PAIR_PREFIXES) + ')'
MATCH_STRING += MATCH_PAIR_VALUE
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_PAIR_SUFFIXES) + ')'
MATCH_STRING += '|'
MATCH_STRING += '(' + '|'.join(re.escape(item) for item in MATCH_STANDALONE_PREFIXES) + ')'
MATCH_STRING += MATCH_STANDALONE_VALUE
if not type(SUBREDDITS) == list or len(SUBREDDITS) == 0 or "all" in SUBREDDITS:
    print("Invalid Configuration!")
    sys.exit(0)
REDDIT = None
def reddit():
    global REDDIT
    if REDDIT is None:
        REDDIT = praw.Reddit(user_agent      = Config.USERAGENT,
                             client_id       = Config.APP_ID,
                             client_secret   = Config.APP_SECRET,
                             username        = Config.USERNAME,
                             password        = Config.PASSWORD)
    return REDDIT