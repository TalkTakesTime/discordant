import discord
from configparser import ConfigParser
import sys


class Discordant(discord.Client):
    def __init__(self):
        super().__init__()

        # TODO: move this elsewhere (to own function?)
        try:
            config = ConfigParser()
            config.read('config.ini')
            self.email = config.get('Login', 'email')
            self.password = config.get('Login', 'password')
        except FileNotFoundError:
            print("No config file found (expected 'config.ini').")
            print(("Copy config-example.ini to config.ini and edit it to "
                   "use the appropriate settings."))
            sys.exit(-1)

        self.login(self.email, self.password)

    def on_message(self, message):
        # this is just a pointless little handler
        # TODO: expand to a proper event handler which can match arbitrary
        # message events -- using regex?
        # also TODO: logging
        if message.content.lower() == 'ping':
            self.send_message(message.channel,
                              message.content.replace('i', 'o').
                                              replace('I', 'O'))
