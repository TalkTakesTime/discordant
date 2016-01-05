import discord
from configparser import ConfigParser
from os import path
import sys
import re
from threading import Thread


class Discordant(discord.Client):
    _handlers = {}
    _triggers = set()

    def __init__(self, config_file='config.ini'):
        super().__init__()

        self.email = ''
        self.password = ''
        self.command_char = ''
        self._config = ConfigParser()

        self._load_config(config_file)
        self.login(self.email, self.password)

    def _load_config(self, config_file):
        if not path.exists(config_file):
            print("No config file found (expected '{}').".format(config_file))
            print("Copy config-example.ini to", config_file,
                  "and edit it to use the appropriate settings.")
            sys.exit(-1)

        self._config.read(config_file)
        self.email = self._config.get('Login', 'email')
        self.password = self._config.get('Login', 'password')

    def on_message(self, message):
        # TODO: logging
        for handler_name, trigger in Discordant._handlers.items():
            match = trigger.search(message.content)
            if match is not None:
                Thread(target=getattr(self, handler_name),
                       args=(match, message)).start()
            # do we return after the first match? or allow multiple matches

    @classmethod
    def register_handler(cls, trigger, regex_flags=0):
        try:
            trigger = re.compile(trigger, regex_flags)
        except re.error as err:
            print('Invalid trigger "{}": {}'.format(trigger, err.msg))
            sys.exit(-1)

        if trigger.pattern in cls._triggers:
            print('Cannot reuse pattern "{}"'.format(trigger.pattern))
            sys.exit(-1)

        cls._triggers.add(trigger.pattern)

        def wrapper(func):
            func_name = '_cmd_' + func.__name__
            # disambiguate the name if another handler has the same name
            while func_name in cls._handlers:
                func_name += '_'

            setattr(cls, func_name, func)
            cls._handlers[func_name] = trigger

        return wrapper
