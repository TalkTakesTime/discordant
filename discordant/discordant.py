import discord
from configparser import ConfigParser
import sys
import re


class Discordant(discord.Client):
    _handlers = {}
    _triggers = set()

    def __init__(self, config_file='config.ini'):
        super().__init__()

        # TODO: move this elsewhere (to own function?)
        try:
            config = ConfigParser()
            config.read(config_file)
            self.email = config.get('Login', 'email')
            self.password = config.get('Login', 'password')
        except FileNotFoundError:
            print("No config file found (expected '{}').".format(config_file))
            print("Copy config-example.ini to", config_file,
                  "and edit it to use the appropriate settings.")
            sys.exit(-1)

        self.login(self.email, self.password)

    def on_message(self, message):
        # TODO: logging
        for handler_name, trigger in Discordant._handlers.values():
            print('trying', handler_name, 'with', trigger.pattern)
            match = trigger.search(message.content)
            if match is not None:
                # TODO: do this in a new thread
                getattr(self, handler_name)(match, message)
            # do we return after the first match? or allow multiple matches

    @classmethod
    def register_handler(cls, trigger, flags=0):
        try:
            trigger = re.compile(trigger, flags)
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
