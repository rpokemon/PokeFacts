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
import time
import praw
import codecs
import prawcore
import importlib
import traceback

from praw.models.util import stream_generator

try:
    from PokeFacts import Config
    from PokeFacts import DataPulls
    from PokeFacts import Helpers
    from PokeFacts import Management
    from PokeFacts import Responder
except ImportError:
    import Config
    import DataPulls
    import Helpers
    import Management
    import Responder
try:
    from layer7_utilities import Logger
except ImportError:
    class Logger():
        def __init__(self, botname, botversion):
            self.botname = botname
            self.botversion = botversion
        def info(self, msg):
            print(self.botname + " v"+self.botversion+" [INFO] : " + msg)
        def debug(self, msg):
            print(self.botname + " v"+self.botversion+" [DEBUG] : " + msg)
        def warning(self, msg):
            print(self.botname + " v"+self.botversion+" [WARNING] : " + msg)
        def exception(self, msg):
            print(self.botname + " v"+self.botversion+" [EXCEPTION] : " + msg)
        def critical(self, msg):
            print(self.botname + " v"+self.botversion+" [CRITICAL] : " + msg)
        def error(self, msg):
            print(self.botname + " v"+self.botversion+" [ERROR] : " + msg)

# Call the bot, get a response...
class CallResponse():
    def __init__(self):
        self.startTime  = time.time()
        self.scriptfile = os.path.abspath(__file__)
        self.scriptpath = os.path.dirname(self.scriptfile)
        self.logger     = Logger(Config.USERNAME, Config.VERSION)

        self.r = Config.reddit()
        self.logger.info('Connected to reddit account: {}'.format(self.r.user.me()))

        self.helpers    = Helpers.Helpers(self.r)
        self.mgmt       = Management.Management(self)
        self.data       = DataPulls.DataPulls(self)
        self.done       = {}
        
        self.reloadConfig(True)
    
    # Reload the configuration. If the Config.py file was modified, this
    # function will make those changes go into effect
    def reloadConfig(self, first_load=False):
        if not first_load:
            importlib.reload(Config)
        
        self.match_p    = re.compile(Config.MATCH_STRING)
        self.subreddit  = self.r.subreddit('+'.join(Config.SUBREDDITS))
        self.srmodnames = list(sr.lower() for sr in Config.SUBREDDITS if self.helpers.isBotModeratorOf(sr, 'posts'))
        self.srNoTry    = [] # list of subreddit (IDs) to not operate in

        if any(self.srmodnames):
            self.modded = self.r.subreddit('+'.join(self.srmodnames))
        else:
            self.modded = None
        
        template_file = codecs.open(self.scriptpath + '/' + Config.REPLY_TEMPLATE_FILE.lstrip('/'), "r", "utf-8")
        self.response_template = template_file.read()
        template_file.close()

        self.logger.info('Initialized and ready to go on: ' + (', '.join(Config.SUBREDDITS)))

    # get a list of call items in the given body
    # list will be empty if the bot was not called
    def get_calls(self, body):
        items = []
        seen  = []

        it = re.finditer(self.match_p, body)
        for match in it:
            match = match.group(0)

            identifier, prefix = self.helpers.validateIdentifier(match)
            
            if identifier in seen:
                continue
            else:
                seen.append(identifier)

            if not identifier == False:
                info = self.data.getInfo(identifier, prefix)
                if not info is None:
                    self.logger.debug("Got info for: %s"%match)
                    items.append(info)
        
        return items
    
    # will compile the response for the bot to send given a list of call items
    def get_response(self, parent_thing, items):
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
            'body':         response_body,
        })
    
    # called from 'process' method, returns True
    # if should break out of the current stream after
    # the current thing is processed
    def should_break(self, thing):
        # if the thing was created before the bot initialized
        if thing.created_utc < self.startTime:
            return True

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
            else:
                if thing.edited == False:
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
    def process(self, thing, ignore_break=False):
        if hasattr(thing, 'subreddit') and not thing.subreddit is None and thing.subreddit.id in self.srNoTry:
            return True

        ttype       = self.helpers.typeof(thing)        # thing type (int)
        noun        = self.helpers.nounForType(ttype)   # thing type noun
        is_valid    = True                              # if the thing is valid for processing
        subject     = None                              # thing subject (if applicable)
        body        = None                              # thing body
        items       = []                                # call items

        if self.should_break(thing):
            if not ignore_break:
                return False

        if ttype == Helpers.COMMENT:
            body      = thing.body
            is_valid  = self.helpers.isValidComment(thing)
        elif ttype == Helpers.SUBMISSION:
            body      = thing.selftext
            is_valid  = self.helpers.isValidSubmission(thing)
        elif ttype == Helpers.MESSAGE:
            body      = thing.body
            subject   = thing.subject
            is_valid  = self.helpers.isValidMessage(thing) # returns False
            if thing.author is not None and thing.author.name in Config.OPERATORS:
                response = self.mgmt.processOperatorCommand(thing.author.name, subject, body)
                if type(response) == str:
                    thing.reply(response)

        if not is_valid:
            return True
        
        items           = self.get_calls(body)
        reply_thing     = None                      # the comment created by the bot's reply

        if any(items):
            self.logger.debug("Got " + str(len(items)) + " calls from " + thing.fullname)
            try:
                # compile reply
                response_body = self.get_response(thing, items)

                # check if already there already exists a reply for this thing
                if thing.id in self.done:
                    reply_thing = self.r.comment(id=self.done[thing.id]["reply_id"])
                    reply_thing.edit(response_body)
                    self.logger.info("> Edited reply to " + noun + " by %s, id - %s"%(str(thing.author), thing.fullname))
                else:
                    reply_thing = thing.reply(response_body)
                    self.logger.info("> Replied to " + noun + " by %s, id - %s"%(str(thing.author), thing.fullname))

                    # optionals
                    if self.mgmt.bot_isModerator(thing.subreddit):
                        if ttype == Helpers.SUBMISSION and Config.REPLY_SHOULD_STICKY:
                            reply_thing.mod.distinguish(sticky=True)
                        elif ttype == Helpers.COMMENT and Config.REPLY_SHOULD_DISTINGUISH:
                            reply_thing.mod.distinguish()

                # add to done queue
                self.done[thing.id] = {
                    "reply_id":  reply_thing.id,
                    "last_process": time.time()
                }
            except praw.exceptions.APIException:
                self.logger.warning("> " + noun + " was deleted, id - %s"%str(thing.fullname))
            except prawcore.exceptions.Forbidden:
                # we're banned from this subreddit, add to self.srNoTry
                # so we won't try again for this subbie
                self.srNoTry.append(thing.subreddit.id)
            except Exception as e:
                # delete if something went wrong with generating the reply
                reply_thing.delete()
                reply_thing = None
                self.logger.warning("> [1] Was unable to reply to: " + thing.fullname)
                print(traceback.format_exception(None, e, e.__traceback__),
                        file=sys.stderr, flush=True)

        return True

    # main loop action
    def action(self):
        self.logger.debug("<<<Next Loop>>>")

        # check comments
        if Config.RESPONDER_CHECK_COMMENTS:
            self.logger.debug('-----[ Checking new comments ]-----')
            for comment in self.subreddit.comments(limit=200):
                if comment is None:
                    break
                if not self.process(comment):
                    break
        
        # check self posts
        if Config.RESPONDER_CHECK_SUBMISSIONS:
            self.logger.debug('-----[ Checking new submissions ]-----')
            for submission in self.subreddit.new(limit=100):
                if submission is None:
                    break
                if not self.process(submission):
                    break

        # check edited comments for modded subs
        if Config.RESPONDER_CHECK_EDITED and not self.modded is None:
            self.logger.debug('-----[ Checking edited comments ]-----')
            for edited_thing in self.modded.mod.edited(limit=100):
                if edited_thing is None:
                    break
                if not self.process(edited_thing):
                    break
                    
        # check messages (for operator sent commands)
        self.logger.debug('-----[ Checking unread inbox ]-----')
        for message in self.r.inbox.unread(limit=None):
            if message is None:
                break

            message.mark_read()

            if message.subject == 'username mention':
                print("got mention: " + message.fullname)
                if not Config.RESPONDER_CHECK_MENTIONS:
                    continue
                print(" - will proceed to processing")

            self.process(message, ignore_break = True)

def main(redditbot):
    try:
        redditbot.action()

    except UnicodeEncodeError as e:
        redditbot.logger.warning("Caught UnicodeEncodeError")
        print(traceback.format_exception(None, e, e.__traceback__),
                file=sys.stderr, flush=True)
 
    except praw.exceptions.APIException as e:
        redditbot.logger.exception("API Error! - Sleeping")
        print(traceback.format_exception(None, e, e.__traceback__),
                file=sys.stderr, flush=True)
        time.sleep(120)

    except praw.exceptions.ClientException as e:
        redditbot.logger.exception("PRAW Client Error! - Sleeping")
        print(traceback.format_exception(None, e, e.__traceback__),
                file=sys.stderr, flush=True)
        time.sleep(120)

    except prawcore.exceptions.ServerError as e:
        redditbot.logger.exception("PRAW Server Error! - Sleeping")
        print(traceback.format_exception(None, e, e.__traceback__),
                file=sys.stderr, flush=True)
        time.sleep(120)

    except KeyboardInterrupt:
        redditbot.logger.warning('Caught KeyboardInterrupt')
        sys.exit()
        
    except Exception as e:
        redditbot.logger.critical('General Exception - sleeping 5 min')
        print(traceback.format_exception(None, e, e.__traceback__),
                file=sys.stderr, flush=True)
        time.sleep(300)

if __name__ == '__main__':
    redditbot = CallResponse()
    while True:
        main(redditbot)