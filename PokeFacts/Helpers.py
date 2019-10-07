#!/usr/bin/env python3

# Helpers.py
# ~~~~~~~~~~
# helper functions and things

import unicodedata
import prawcore
import re

try:
    from . import config
except ImportError:
    import config

COMMENT = 1
ACCOUNT = 2
SUBMISSION = 3
MESSAGE = 4
SUBREDDIT = 5
AWARD = 6
PROMOCAMPAIGN = 8


class Helpers():

    # main - CallResponse instance
    def __init__(self, praw_reddit):
        self.reddit = praw_reddit

    def is_valid_thing(self, thing):
        # don't reply to banned/suspended users
        if thing.author is None:
            return False

        # the bot shouldn't reply to itself
        if thing.author.name == config.USERNAME:
            return False

        return True

    def is_valid_comment(self, comment):
        if not self.is_valid_thing(comment):
            return False

        is_foreign_comment = comment.subreddit.display_name in config.SUBREDDITS

        # if a foreign comment, assume it was a mention from a foreign subreddit
        if is_foreign_comment and not config.RESPONDER_CHECK_MENTIONS_OTHER_SUBREDDITS:
            return False

        return True

    def is_valid_submission(self, submission):
        if not self.is_valid_thing(submission):
            return False
        return submission.is_self  # we only want self posts

    def is_valid_message(self, message):
        return False

    def validate_identifier(self, query):
        if len(query) <= 1:
            return False, None

        if config.IDENTIFIER_NO_ACCENTS:
            query = Helpers.remove_accents(query)

        if config.IDENTIFIER_TO_LOWER:
            query = query.lower()

        prefix_cache = {}

        def find_prefix(options):
            idx = 0

            for opt in options:
                opt_len = len(opt)

                if opt_len not in prefix_cache:
                    prefix_cache[opt_len] = query[:opt_len]

                if prefix_cache[opt_len] == opt:
                    break

                idx += 1

            if idx == len(options):
                return -1, 0

            return idx, len(options[idx])

        idx, offset = find_prefix(config.MATCH_PAIR_PREFIXES)

        # if no results for pair prefixes, try standalone prefixes
        if idx == -1:
            idx, offset = find_prefix(config.MATCH_STANDALONE_PREFIXES)

            # if still no results, return false
            if idx == -1:
                return False, None

            identifier = query[offset:]
            prefix = config.MATCH_STANDALONE_PREFIXES[idx]
        else:
            suffix = config.MATCH_PAIR_SUFFIXES[idx]
            suffix_len = len(suffix)

            if not query[-suffix_len:] == suffix:
                return False, None

            identifier = query[offset:-suffix_len]
            prefix = config.MATCH_PAIR_PREFIXES[idx]

        if type(config.IDENTIFIER_SANITIZE) == str:
            identifier = re.sub(config.IDENTIFIER_SANITIZE,
                                '', identifier)  # remove symbols

        # remove extraneous whitespace
        identifier = re.sub(r'\s+', ' ', identifier).strip()

        return identifier, prefix

    # removes accents
    # e.g. "Flabébé" -> "Flabebe"
    @staticmethod
    def remove_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')

    def typeof(self, x):
        if not type(x) == str:
            try:
                x = x.fullname
            except NameError:
                return False
            except AttributeError:
                return False
            except prawcore.exceptions.NotFound:
                return False

        try:
            ret = int(x.split('_')[0][1:])
            if ret < 1 or ret > 8:
                return False
            return ret
        except Exception:
            return False

    def noun_for_type(self, type):
        if type == COMMENT:
            return 'comment'
        elif type == ACCOUNT:
            return 'account'
        elif type == SUBMISSION:
            return 'submission'
        elif type == MESSAGE:
            return 'message'
        elif type == SUBREDDIT:
            return 'subreddit'
        elif type == AWARD:
            return 'award'
        elif type == PROMOCAMPAIGN:
            return 'promo campaign'

    # Is the bot the parent of the given comment?

    def is_bot_the_parent(self, comment):
        if not self.reddit:
            return False

        try:
            parent_comment = self.reddit.comment(id=comment.parent_id)

            return parent_comment.author.name == config.USERNAME
        except Exception:
            return False

    # is the given comment a top level comment?
    def is_top_level_comment(self, comment):
        try:
            return self.typeof(comment.parent_id) == SUBMISSION
        except Exception:
            return False

    def is_bot_moderator_of(self, subreddit, must_have_perms=[]):
        if not self.reddit:
            return False

        if type(subreddit) == str:
            subreddit = self.reddit.subreddit(subreddit)

        if type(must_have_perms) == str:
            must_have_perms = set([must_have_perms])

        if not type(must_have_perms) == set:
            must_have_perms = set(must_have_perms)

        try:
            for mod in subreddit.moderator():
                perms = set(mod.mod_permissions)

                if str(mod) == config.USERNAME:
                    if len(must_have_perms) == 0 or "all" in perms:
                        return True
                    if must_have_perms.issubset(perms):
                        return True
                    return False
        except prawcore.exceptions.Forbidden:
            return False
        return False

    # using permalink() as a function doesn't work on submissions
    # using permalink as an attribute sometimes works and sometimes doesn't work with comments
    def get_permalink(self, thing):
        try:
            return thing.permalink()
        except Exception:
            try:
                return thing.permalink
            except Exception:
                return None
