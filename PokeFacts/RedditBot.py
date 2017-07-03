#!/usr/bin/env python3

# RedditBot.py
# ~~~~~~~~~~~~
# This is the main class of the bot where PRAW
# gets initialized and where the main loop is
#
# First a new instance of CallResponse is created as "redditbot"
# Then the 'main' function is called in an infinite loop
#   - the main function calls redditbot.action() in a large try-catch
# The 'action' function checks various streams (comments, submissions, etc.)
# It passes on the stream things to the 'process' functions, the process
# function determines if it will respond to the thing. If so, it invokes
# 'get_calls' to see if the given thing called the bot.
# If there are no calls, the thing is ignored. Otherwise it passes the result
# of 'get_calls' on the Responder, which'll return the response body back to
# the 'process' function and the process function will reply.

import os
import re
import sys
import imp
import time
import praw
import prawcore

from praw.models.util import stream_generator

from PokeFacts import Config
from PokeFacts import DataPulls
from PokeFacts import Helpers
from PokeFacts import Management
from PokeFacts import Responder

from layer7_utilities import Logger

# Call the bot, get a response...
class CallResponse():
    def __init__(self):
        self.startTime  = time.time()
        self.scriptfile = os.path.abspath(__file__)
        self.logger     = Logger(Config.USERNAME, Config.VERSION)

        self.r = Config.reddit()
        self.logger.info('Connected to reddit account: {}'.format(self.r.user.me()))

        self.helpers    = Helpers.Helpers(self.r)
        self.mgmt       = Management.Management(self)
        self.data       = DataPulls.DataPulls(self)
        self.done       = {}
        
        self.reloadConfig(True)
        self.logger.info('Initialized and ready to go on: ' + (', '.join(Config.SUBREDDITS)))
    
    # Reload the configuration. If the Config.py file was modified, this
    # function will make those changes go into effect
    def reloadConfig(self, first_load=False):
        if not first_load:
            imp.reload(Config)

        self.subreddit  = self.r.subreddit('+'.join(Config.SUBREDDITS))
        self.srmodnames = (sr.lower() for sr in Config.SUBREDDITS if self.helpers.isBotModeratorOf(sr, 'posts'))
        self.modded     = self.r.subreddit('+'.join(self.srmodnames))
        self.srNoTry    = [] # list of subreddit (IDs) to not operate in

        with open('data/response.txt', 'r') as template_file:
            self.response_template = template_file.read()

    # get a list of call items in the given body
    # list will be empty if the bot was not called
    def get_calls(self, body):
        items = []
        seen  = []

        for match in re.findall(Config.MATCH_STRING, body):
            identifier = self.helpers.validateIdentifier(match)
            
            if identifier in seen:
                continue
            else:
                seen.append(identifier)

            if not identifier == False:
                info = self.data.getInfo(identifier)
                if info:
                    self.logger.debug("Got info for: %s"%match)
                    items.append()
        return items
    
    # will compile the response for the bot to send given a list of call items
    def get_response(self, parent_thing, reply_thing, items):
        response_body = ''

        for item in items[:-1]:
            response_body += Responder.getResponse(item)
        else:
            response_body += Responder.getResponse(items[-1], True)

        return self.response_template.format(** {
            'author':       parent_thing.author.name,
            'subreddit':    parent_thing.subreddit.display_name,
            'permalink':    self.helpers.getPermalink(parent_thing),
            'botname':      Config.USERNAME,
            'reply_id':     reply_thing.id,
            'reply_utc':    reply_thing.created_utc,
            'reply_link':   self.helpers.getPermalink(reply_thing),
            'body':         response_body,
        })
    
    # called from 'process' method, returns True
    # if should break out of the current stream after
    # the current thing is processed
    def should_break(self, thing):
        seen = False
        if thing.id in self.done:
            last_process = self.done[thing.id]['last_process']
            seen = True

        if not seen:
            return False
        else:
            # if the comment has been seen, only do not break if
            # the comment's edit time after the last process time

            if not hasattr(thing, 'edited'):
                return True
            elif thing.edited == False:
                return True
            elif thing.edited > last_process:
                return False
            else:
                return True
    
    # process the thing (comment, submission, or message)
    #  - responds if necessary
    #  - edits previous response if already responded
    #  - this function does NOT check if the thing is from an approved
    #    subreddit, the 'action' function takes care of those checks
    # Returns:
    #   true - if should continue
    #   false - if should break
    def process(self, thing, ignore_done = False):
        if hasattr(thing, 'subreddit') and thing.subreddit.id in self.srNoTry:
            return True

        type        = self.helpers.typeof(thing)        # thing type (int)
        noun        = self.nounForType(type)            # thing type noun
        is_valid    = True                              # if the thing is valid for processing
        subject     = None                              # thing subject (if applicable)
        body        = None                              # thing body
        items       = []                                # call items

        if self.should_break(thing):
            return False

        if type == Helpers.COMMENT:
            body      = thing.body
            is_valid  = self.helpers.isValidComment(thing)
        elif type == Helpers.SUBMISSION:
            body      = thing.selftext
            is_valid  = self.helpers.isValidSubmission(thing)
        elif type == Helpers.MESSAGE:
            body      = thing.body
            subject   = thing.subject
            is_valid  = self.helpers.isValidMessage(thing) # return False
            if thing.author.name in Config.OPERATORS:
                self.mgmt.processOperatorCommand(thing.author.name, subject, body)

        if not is_valid:
            return True
        
        items           = self.get_calls(body)
        reply_thing     = None                      # the comment created by the bot's reply
        did_edit        = False                     # if the bot edited an existing comment

        if any(items):
            try:
                # check if already there already exists a reply for this thing
                if thing.id in self.done:
                    reply_thing  = self.r.comment(id=self.done[thing.id]["reply_id"])
                    did_edit     = True
                else:
                    # reply without body first so that we can pass the thing id and permalink
                    # on to the response generator function
                    try:
                        reply_thing = thing.reply("&nbsp;")
                    except prawcore.exceptions.Forbidden:
                        # we're banned from this subreddit, add to self.srNoTry
                        # so we won't try again for this subbie
                        self.srNoTry.append(thing.subreddit.id)
                        reply_thing = None
                if reply_thing:
                    try:
                        # compile reply
                        response_body = self.get_response(thing, reply_thing, items)
                        reply_thing.edit(response_body)
                        self.logger.info("Replied to " + noun + " by %s, id - %s"%(str(thing.author), thing.fullname))
                        
                        # optionals
                        if not did_edit and self.mgmt.bot_isModerator(thing.subreddit):
                            if type == Helpers.SUBMISSION and Config.REPLY_SHOULD_STICKY:
                                reply_thing.mod.distinguish(sticky=True)
                            elif type == Helpers.COMMENT and Config.REPLY_SHOULD_DISTINGUISH:
                                reply_thing.mod.distinguish()

                        # add to done queue
                        self.done[thing.id] = {
                            "reply_id":  reply_thing.id,
                            "last_process": time.time()
                        }
                    except:
                        # delete if something went wrong with generating the reply
                        reply_thing.delete()
                        reply_thing = None
            except praw.exceptions.APIException:
                self.logger.warning(noun + " was deleted, id - %s"%str(thing.fullname))

        return True

    # main loop action
    def action(self):
        # check comments
        if Config.RESPONDER_CHECK_COMMENTS:
            for comment in self.subreddit.stream.comments():
                if comment is None:
                    break
                if not self.process(comment):
                    break
        
        # check self posts
        if Config.RESPONDER_CHECK_SUBMISSIONS:
            for submission in self.subreddit.stream.submissions():
                if submission is None:
                    break
                if not self.process(submission):
                    break

        # check user name mentions (for edited comments)
        if Config.RESPONDER_CHECK_MENTIONS:
            for comment in self.r.inbox.mentions(limit=None):
                if comment is None:
                    break
                if not self.process(comment):
                    break

        # check edited comments for modded subs
        if Config.RESPONDER_CHECK_EDITED:
            editstream = stream_generator(self.modded.mod.edited,pause_after=0)
            for edited_thing in editstream:
                if edited_thing is None:
                    break
                if not self.process(edited_thing):
                    break
                    
        # check messages (for operator sent commands)
        for message in self.r.inbox.unread(limit=10):
            if message is None:
                break
            if not self.process(message):
                break

def main(redditbot):
    try:
        redditbot.action()

    except UnicodeEncodeError:
        redditbot.logger.warning("Caught UnicodeEncodeError")
 
    except praw.exceptions.APIException:
        redditbot.logger.exception("API Error! - Sleeping")
        time.sleep(120)

    except praw.exceptions.ClientException:
        redditbot.logger.exception("PRAW Client Error! - Sleeping")
        time.sleep(120)

    except prawcore.exceptions.ServerError:
        redditbot.logger.exception("PRAW Server Error! - Sleeping")
        time.sleep(120)

    except KeyboardInterrupt:
        redditbot.logger.warning('Caught KeyboardInterrupt')
        sys.exit()
        
    except Exception:
        redditbot.logger.critical('General Exception - sleeping 5 min')
        time.sleep(300)

if __name__ == '__main__':
    redditbot = CallResponse()
    redditbot.logger.info("Starting up")
    while True:
        main(redditbot)