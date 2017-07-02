#!python3

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

import time, re, sys
import praw, prawcore
from praw.models.util import stream_generator

import Config
import DataPulls
import Helpers
import Responder

from layer7_utilities import Logger

# Call the bot, get a response...
class CallResponse():
    def __init__(self):
        self.logger = Logger(Config.USERNAME, Config.VERSION)

        self.login()
        self.done       = {} # thing id -> bot response comment (or None if not yet responded) map
        self.startTime  = time.time()
        self.helpers    = Helpers.Helpers(self)
        self.subreddit  = self.r.subreddit('+'.join(Config.SUBREDDITS))
        self.modded     = self.r.subreddit('+'.join(
                                sr for sr in Config.SUBREDDITS if self.helpers.isBotModeratorOf(sr, 'posts') ))

        self.logger.info('Initialized and ready to go on: ' + (', '.join(Config.SUBREDDITS)))
    
    # login to reddit
    def login(self):
        self.r = praw.Reddit(user_agent      = Config.USERAGENT,
                             client_id       = Config.APP_ID,
                             client_secret   = Config.APP_SECRET,
                             username        = Config.USERNAME,
                             password        = Config.PASSWORD)
                        
        self.logger.info('Connected to reddit account: {}'.format(self.r.user.me()))

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
                self.logger.debug("Getting info for: %s"%match)
                items.append(DataPulls.getInfo(identifier))
        return items
    
    # will compile the response for the bot to send given a list of call items
    def get_response(self, thing, items):
        return Responder.getResponse(thing, items)
    
    # process the thing (comment, submission, or message)
    #  - responds if necessary
    #  - edits previous response if already responded
    #  - this function does NOT check if the thing is from an approved
    #    subreddit, the 'action' function takes care of those checks
    def process(self, thing):
        type  = self.helpers.typeof(thing)      # thing type
        noun  = self.nounForType(type)
        items = []                              # call items

        if type == Helpers.COMMENT:
            if not self.helpers.isValidComment(thing):
                return
            items = self.get_calls(thing.body)
        elif type == Helpers.SUBMISSION:
            if not self.helpers.isValidSubmission(thing):
                return
            items = self.get_calls(thing.selftext)
        elif type == Helpers.MESSAGE:
            pass # ignore messages
        
        reply_thing = None  # the comment created by the bot's reply
        did_edit = False    # if the bot edited an existing comment rather than creating a new one

        if any(items):
            try:
                # check if already there already exists a reply for this thing
                if thing.id in self.done:
                    reply_thing = self.r.comment(id=self.done[thing.id])
                
                # compile reply
                response_body = self.get_response(thing, items)

                if reply_thing is None:
                    # create reply
                    reply_thing = thing.reply(response_body)
                    self.logger.info("Replied to " + noun + " by %s, id - %s"%(str(thing.author), thing.fullname))

                else:
                    # edit existing reply if exists
                    reply_thing.edit(response_body)
                    did_edit = True
                    self.logger.info("Edited reply to " + noun + " by %s, id - %s"%(str(thing.author), thing.fullname))
            except praw.exceptions.APIException:
                self.logger.warning(noun + " was deleted, id - %s"%str(thing.fullname))
        
        if reply_thing and not did_edit:
            if type == Helpers.SUBMISSION and Config.REPLY_SHOULD_STICKY:
                reply_thing.mod.distinguish(sticky=True)
            elif type == Helpers.COMMENT and Config.REPLY_SHOULD_DISTINGUISH:
                reply_thing.mod.distinguish()
        
        self.done[thing.id] = reply_thing.id

    # main loop action
    def action(self):
        # check comments
        if Config.RESPONDER_CHECK_COMMENTS:
            for comment in self.subreddit.stream.comments():
                if comment is None:
                    break
                self.process(comment)
        
        # check self posts
        if Config.RESPONDER_CHECK_SUBMISSIONS:
            for submission in self.subreddit.stream.submissions():
                if submission is None:
                    break
                self.process(submission)

        # check user name mentions (for edited comments)
        if Config.RESPONDER_CHECK_MENTIONS:
            for comment in self.r.inbox.mentions(limit=None):
                if comment is None:
                    break
                
                # skip if not actually a comment (just in case)
                if not self.helpers.typeof(comment.fullname) == Helpers.COMMENT:
                    continue

                # skip if not from config approved subreddit
                if not Config.RESPONDER_CHECK_MENTIONS_OTHER_SUBREDDITS \
                        and not comment.subreddit.display_name in Config.SUBREDDITS:
                    continue

                self.process(comment)

        # check edited comments for modded subs
        if Config.RESPONDER_CHECK_EDITED:
            editstream = stream_generator(self.modded.mod.edited,pause_after=0)
            for edited_thing in editstream:
                if edited_thing is None:
                    break
                self.process(edited_thing)

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