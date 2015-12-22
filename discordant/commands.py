from .discordant import Discordant
import re


@Discordant.register_handler(r'^ping$', re.I)
def ping(self, match, message):
    self.send_message(message.channel, 'pong')
