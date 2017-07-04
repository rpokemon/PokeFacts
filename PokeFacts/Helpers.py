#!/usr/bin/env python3

# Helpers.py
# ~~~~~~~~~~
# helper functions and things

import unicodedata
import prawcore
import re

try:
    from PokeFacts import Config
except ImportError:
    import Config

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

    def isValidThing(self, thing):
        # the bot shouldn't reply to itself
        if thing.author.name == Config.USERNAME:
            return False

        return True

    def isValidComment(self, comment):
        if not self.isValidThing(comment):
            return False
        
        is_foreign_comment = comment.subreddit.display_name in Config.SUBREDDITS
        
        # if a foreign comment, assume it was a mention from a foreign subreddit
        if is_foreign_comment and not Config.RESPONDER_CHECK_MENTIONS_OTHER_SUBREDDITS:
            return False

        return True

    def isValidSubmission(self, submission):
        if not self.isValidThing(submission):
            return False
        return submission.is_self # we only want self posts

    def isValidMessage(self, message):
        return False

    def validateIdentifier(self, query):
        if len(query) <= 1:
            return False
        
        if Config.IDENTIFIER_NO_ACCENTS:
            query = self.removeAccents(query)

        if Config.IDENTIFIER_TO_LOWER:
            query = query.lower()
        
        prefix_cache = {}
        
        def find_prefix(options):
            idx = 0

            for opt in options:
                opt_len = len(opt)

                if not opt_len in prefix_cache:
                    prefix_cache[opt_len] = query[:opt_len]

                if prefix_cache[opt_len] == opt:
                    break
                
                idx += 1

            if idx == len(options):
                return -1, 0

            return idx, len(options[idx])

        idx, offset = find_prefix(Config.MATCH_PAIR_PREFIXES)

        # if no results for pair prefixes, try standalone prefixes
        if idx == -1:
            idx, offset = find_prefix(Config.MATCH_STANDALONE_PREFIXES)

            # if still no results, return false
            if idx == -1:
                return False

            identifier = query[offset:]
        else:
            suffix = Config.MATCH_PAIR_SUFFIXES[idx]
            suffix_len = len(suffix)

            if not query[-suffix_len:] == suffix:
                return False

            identifier = query[offset:-suffix_len]
        
        if type(Config.IDENTIFIER_SANITIZE) == str:
            identifier = re.sub(Config.IDENTIFIER_SANITIZE, '', identifier) # remove symbols

        identifier = re.sub(r'\s+', ' ', identifier).strip() # remove extraneous whitespace

        return identifier

    # removes accents
    # e.g. "Flabébé" -> "Flabebe"
    def removeAccents(self, s):
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
        except:
            return False

    def nounForType(self, type):
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
    def isBotTheParent(self, comment):
        try:
            parentComment = self.reddit.comment(id=comment.parent_id)

            return parentComment.author.name == Config.USERNAME
        except:
            return False

    # is the given comment a top level comment?
    def isTopLevelComment(self, comment):
        try:
            return self.typeof(comment.parent_id) == SUBMISSION
        except:
            return False

    def isBotModeratorOf(self, subreddit, must_have_perms = []):
        if type(subreddit) == str:
            subreddit = self.reddit.subreddit(subreddit)
            
        if type(must_have_perms) == str:
            must_have_perms = set([must_have_perms])

        if not type(must_have_perms) == set:
            must_have_perms = set(must_have_perms)

        for mod in subreddit.moderator():
            perms = set(mod.mod_permissions)

            if str(mod) == Config.USERNAME:
                if len(must_have_perms) == 0 or "all" in perms:
                    return True
                if must_have_perms.issubset(perms):
                    return True
                return False
                
        return False

    # using permalink() as a function doesn't work on submissions
    # using permalink as an attribute sometimes works and sometimes doesn't work with comments
    def getPermalink(self, thing):
        try:
            return thing.permalink()
        except:
            try:
                return thing.permalink
            except:
                return None