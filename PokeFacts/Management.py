#!/usr/bin/env python3

import os
import sys
import praw
import psutil
import signal

class Management():

    def __init__(self, main):
        self.main = main

    # If a reddit user whose username is in the Config.OPERATORS list
    # sends a private message to the bot, this method will be called.
    def processOperatorCommand(self, operator, subject, body):
        self.main.logger.info('Got operator command from ' + str(operator) + ': ' + subject)

        operator_commands = {
            "ReloadData":       self.bot_reloadData,
            "ReloadConfig":     self.bot_reloadConfig,
            "ClearDoneQueue":   self.bot_clearDoneQueue,
            "BotShutdown":      self.bot_shutdown,
            "BotRestart":       self.bot_restart,
        }
        try:
            if operator_commands[subject]():
                return "Command execution succesful."
            else:
                return "Command execution failed."
        except KeyError:
            return False            

    def bot_reloadData(self):
        try:
            self.main.data.reload()
            return True
        except IOError:
            return False

    def bot_reloadConfig(self):
        try:
            self.main.reloadConfig()
            return True
        except IOError:
            return False

    def bot_clearDoneQueue(self):
        self.main.done = {}
        return True

    def bot_shutdown(self):
        sys.exit(0)

    def bot_isNohupMode(self):
        if hasattr(signal, 'SIGHUP'):
            if signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:  # default action
                is_nohup = False
            else:
                is_nohup = True
        else:
            is_nohup = False
        return is_nohup

    def bot_restart(self):
        try:
            # close open files/resources to prevent possible memory leaks
            p = psutil.Process(os.getpid())
            for handler in p.get_open_files() + p.connections():
                os.close(handler.fd)
        except:
            return False

        # restart the current script
        # path, arg0, arg1, ...
        # in the first arg, we add the python executable to the path
        # in the second arg, we run python as the command
        # in the third arg, we specify the python file to run
        # in the remaining args we pass the original arguments
        # if the current script was originally run in nohup mode, that'll carry over
        try:
            os.execl(sys.executable, sys.executable, self.main.scriptfile, *sys.argv[1:])
            return True
        except OSError:
            return False
    
    # does the bot mod with at least 'posts' perms?
    def bot_isModerator(self, subreddit):
        if type(subreddit) == praw.models.reddit.subreddit.Subreddit:
            subreddit = subreddit.display_name
        return subreddit.lower() in self.main.srmodnames