#!/usr/bin/env python3

from PokeFacts import Config

class Management():

    def __init__(self, main):
        self.main = main

    # If a reddit user whose username is in the Config.OPERATORS list
    # sends a private message to the bot, this method will be called.
    def processOperatorCommand(self, operator, subject, body):
        self.main.logger.info('Got operator command from ' + str(operator) + ': ' + subject)

        if subject == "ReloadData":
            self.main.data.reload()
        elif subject == "ReloadConfig":
            self.main.reloadConfig()
        elif subject == "ClearDoneQueue":
            self.main.clearDoneQueue()
        elif subject == "BotShutdown":
            self.main.bot_shutdown()
        elif subject == "BotRestart":
            self.main.bot_restart()