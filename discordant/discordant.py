import discord
from collections import namedtuple
from configparser import ConfigParser
from os import path
import sys
import re
from threading import Thread


Command = namedtuple('Command', ['name', 'arg_func', 'aliases'])


class Discordant(discord.Client):
    _CMD_NAME_REGEX = re.compile(r'[a-z0-9]+')
    _handlers = {}
    _commands = {}
    _aliases = {}
    _triggers = set()

    def __init__(self, config_file='config.ini'):
        super().__init__()

        self.__email = ''  # prevent a conflict with discord.Client#email
        self._password = ''
        self.command_char = ''
        self.config = ConfigParser()

        self.load_config(config_file)
        self.login(self.__email, self._password)

    def load_config(self, config_file):
        if not path.exists(config_file):
            print("No config file found (expected '{}').".format(config_file))
            print("Copy config-example.ini to", config_file,
                  "and edit it to use the appropriate settings.")
            sys.exit(-1)

        self.config.read(config_file)
        self.__email = self.config.get('Login', 'email')
        self._password = self.config.get('Login', 'password')
        self.command_char = self.config.get('Commands', 'command_char')
        self.load_aliases()

    def load_aliases(self):
        aliases = self.config['Aliases']
        for base_cmd, alias_list in aliases.items():
            alias_list = alias_list.split(',')
            cmd_name = self._aliases[base_cmd]

            for alias in alias_list:
                self._aliases[alias] = cmd_name
                self._commands[cmd_name].aliases.append(alias)

    def on_message(self, message):
        # TODO: logging
        if message.content[0] == self.command_char:
            self.run_command(message)
            return

        for handler_name, trigger in self._handlers.items():
            match = trigger.search(message.content)
            if match is not None:
                Thread(target=getattr(self, handler_name),
                       args=(match, message)).start()
            # do we return after the first match? or allow multiple matches

    def run_command(self, message):
        cmd_name, *args = message.content.split(' ')
        cmd_name = cmd_name[1:]
        args = ' '.join(args).strip()

        if cmd_name in self._aliases:
            cmd = self._commands[self._aliases[cmd_name]]
            args = cmd.arg_func(args)
            Thread(target=getattr(self, cmd.name),
                   args=(args, message)).start()

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
            func_name = '_trg_' + func.__name__
            # disambiguate the name if another handler has the same name
            while func_name in cls._handlers:
                func_name += '_'

            setattr(cls, func_name, func)
            cls._handlers[func_name] = trigger

        return wrapper

    @classmethod
    def register_command(cls, name, aliases=None, arg_func=lambda args: args):
        if aliases is None:
            aliases = []
        aliases.append(name)

        def wrapper(func):
            func_name = '_cmd_' + func.__name__
            while func_name in cls._commands:
                func_name += '_'

            setattr(cls, func_name, func)
            cls._commands[func_name] = Command(func_name, arg_func, aliases)
            # associate the given aliases with the command
            for alias in aliases:
                if alias in cls._aliases:
                    print('The alias "{}"'.format(alias),
                          'is already in use for command',
                          cls._aliases[alias][:5].strip('_'))
                    sys.exit(-1)
                if cls._CMD_NAME_REGEX.match(alias) is None:
                    print('The alias "{}"'.format(alias),
                          ('is invalid. Aliases must only contain lowercase'
                           ' letters or numbers.'))
                    sys.exit(-1)
                cls._aliases[alias] = func_name

        return wrapper
