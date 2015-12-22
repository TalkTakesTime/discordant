from .discordant import Discordant
import re


@Discordant.register_handler(r'^ping$', re.I)
def _ping(self, match, message):
    self.send_message(message.channel, message.content.replace('i', 'o').
                                                       replace('I', 'O'))


@Discordant.register_handler(r'\bayy+$', re.I)
def _ayy_lmao(self, match, message):
    self.send_message(message.channel, 'lmao')
