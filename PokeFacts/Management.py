#!/usr/bin/env python3

import os
import sys
import praw
import psutil
import signal
import traceback


class Management():

    def __init__(self, main):
        self.main = main

    # If a reddit user whose username is in the Config.OPERATORS list
    # sends a private message to the bot, this method will be called.
    def process_operator_command(self, operator, subject, body):
        self.main.logger.info('Got operator command from ' +
                              str(operator) + ': ' + subject)

        operator_commands = {
            "ReloadData":       self.bot_reload_data,
            "ReloadConfig":     self.bot_reload_config,
            "ClearDoneQueue":   self.bot_clear_done_queue,
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

    def bot_reload_data(self):
        try:
            self.main.logger.info('Reloading data...')
            self.main.data.reload()
            self.main.logger.info('Data reloaded.')
            return True
        except IOError:
            return False

    def bot_reload_config(self):
        try:
            self.main.reload_config()
            self.main.logger.info('Config reloaded.')
            return True
        except IOError:
            return False

    def bot_clear_done_queue(self):
        self.main.done = {}
        return True

    def bot_shutdown(self):
        sys.exit(0)

    def bot_is_nohup_mode(self):
        if hasattr(signal, 'SIGHUP'):
            if signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:  # default action
                is_nohup = False
            else:
                is_nohup = True
        else:
            is_nohup = False
        return is_nohup

    def bot_restart(self):
        self.main.logger.info('Initializing restart sequence')
        try:
            # close open files/resources to prevent possible memory leaks
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                if not handler.fd == -1:
                    os.close(handler.fd)
            self.main.logger.info('All open files and connections closed')
        except Exception:
            self.main.logger.info(
                'Failed to restart - could not close resources')
            traceback.print_exc()
            return False

        # restart the current script
        # path, arg0, arg1, ...
        # in the first arg, we add the python executable to the path
        # in the second arg, we run python as the command
        # in the third arg, we specify the python file to run
        # in the remaining args we pass the original arguments
        # if the current script was originally run in nohup mode, that'll carry over
        try:
            self.main.logger.info('Restarting...')
            os.execl(sys.executable, sys.executable,
                     self.main.scriptfile, *sys.argv[1:])
            return True
        except OSError:
            self.main.logger.info('Failed to restart - OSError')
            traceback.print_exc()
            return False

    # does the bot mod with at least 'posts' perms?
    def bot_is_moderator(self, subreddit):
        if type(subreddit) == praw.models.reddit.subreddit.Subreddit:
            subreddit = subreddit.display_name
        return subreddit.lower() in self.main.srmodnames
