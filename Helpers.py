#!python3

# Helpers.py
# ~~~~~~~~~~
# helper functions and things

import unicodedata
import prawcore

import Config
import re

COMMENT = 1
ACCOUNT = 2
SUBMISSION = 3
MESSAGE = 4
SUBREDDIT = 5
AWARD = 6
PROMOCAMPAIGN = 8

class Helpers():

    # main - CallResponse instance
    def __init__(self, main):
        self.main = main

    def isValidThing(self, thing):
        # the bot shouldn't reply to itself
        if thing.author.name == Config.USERNAME:
            return False
        
        # if comment was created before the bot initialized
        if thing.created_utc < self.startTime:
            return False

        # if already processed
        if thing.id in self.done:
            return False
        else
            self.done[thing.id] = None

        return True

    def isValidComment(self, comment):
        return self.isValidThing(comment)

    def isValidSubmission(self, submission):
        if not self.isValidThing(submission):
            return False
        
        return submission.is_self # we only want self posts

    def validateIdentifier(self, query):
        if len(query) <= 1:
            return False
        
        if Config.IDENTIFIER_NO_ACCENTS:
            query = self.remove_accents(match)

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

            return idx, options[idx]

        idx, offset = find_prefix(Config.MATCH_PAIR_PREFIXES)

        # if no results for pair prefixes, try standalone prefixes
        if idx == -1:
            idx, offset = find_prefix(Config.MATCH_STANDALONE_PREFIXES)

            # if still no results, return false
            if idx == -1:
                return False

            identifier = query[offset:]
        else:
            cl = Config.MATCH_PAIR_CLOSINGS[idx]
            cl_len = Config.MATCH_PAIR_CLOSINGS[idx]

            if not substr_cache[-cl_len:] == cl:
                return False

            identifier = query[offset:-cl_len]
        
        if type(Config.IDENTIFIER_SANITIZE) == str:
            identifier = re.sub(Config.IDENTIFIER_SANITIZE, '', identifier) # remove symbols

        identifier = re.sub(r'\s+', ' ', identifier).strip()

        return identifier

    # removes accents
    # e.g. "Flabébé" -> "Flabebe"
    def remove_accents(self, s):
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

        x_parts = x.split('_')

        if not len(x_parts) == 2:
            return False

        t_part = x_parts[0]

        if not len(t_part) == 2 or not t_part[:1] == 't':
            return False

        try:
            ret = int(t_part[1:])
            if ret < 1 or ret > 8:
                return False
            return ret
        except ValueError:
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
            parentComment = self.main.r.comment(id=comment.parent_id)

            return parentComment.author.name == Config.USERNAME
        except:
            return False

    # is the given comment a top level comment?
    def isTopLevelComment(self, comment):
        try:
            return typeof(comment.parent_id) == SUBMISSION
        except:
            return False

    def isBotModeratorOf(self, subreddit, must_have_perms = []):
        if type(subreddit) == str:
            subreddit = self.main.r.subreddit(subreddit)
        
        if type(must_have_perms) == str:
            must_have_perms = set([must_have_perms])

        if not type(must_have_perms) == set:
            must_have_perms = set(must_have_perms)

        for mod in subeddit.moderator():
            perms = set(mod.mod_permissions)

            if str(mod) == Config.USERNAME:
                if len(must_have_perms) == 0 or "all" in perms:
                    return True
                if must_have_perms.issubset(perms):
                    return False
                return True
                
        return False