import discord
import logging
import yaml
from sys import stdout, exit


# TODO: make this a method of Discordant
def set_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    format_str = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'

    # log all messages to a log file
    # TODO: allow the user to specify this file, and move this elsewhere
    file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8',
                                       mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(file_handler)

    # log info or higher messages to stdout
    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(stdout_handler)


class Discordant(discord.Client):
    def __init__(self):
        super().__init__()

        # TODO: move this elsewhere (to own function?)
        try:
            with open('config.yaml') as config_file:
                config = yaml.load(config_file)
                self.email = config.get('email')
                self.password = config.get('password')
        except FileNotFoundError:
            print("No config file found (expected 'config.yaml').")
            print(("Copy config-example.yaml to config.yaml and edit it to "
                   "use the appropriate settings."))
            exit(-1)

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


if __name__ == '__main__':
    set_logging()

    bot = Discordant()
    bot.run()
