from .discordant import Discordant
import re
import requests


@Discordant.register_handler(r'^ping$', re.I)
def _ping(self, match, message):
    self.send_message(message.channel,
                      message.content.replace('i', 'o').replace('I', 'O'))


@Discordant.register_handler(r'\bayy+$', re.I)
def _ayy_lmao(self, match, message):
    self.send_message(message.channel, 'lmao')


@Discordant.register_command('youtube')
def _youtube_search(self, args, message):
    base_req_url = 'https://www.googleapis.com/youtube/v3/search'
    req_args = {
        'key': self.config.get('API-Keys', 'youtube'),
        'part': 'snippet',
        'type': 'video',
        'maxResults': 1,
        'q': args
    }

    res = requests.get(base_req_url, req_args)
    if not res.ok:
        self.send_message(message.channel, 'Error:', res.status_code,
                          '-', res.reason)
        return

    json = res.json()
    if json['pageInfo']['totalResults'] == 0:
        self.send_message(message.channel, 'No results found.')
    else:
        self.send_message(message.channel, 'https://youtu.be/' +
                          json['items'][0]['id']['videoId'])


@Discordant.register_command('urban')
def _urban_dictionary_search(self, args, message):
    # this entire function is an egregious violation of the DRY
    # principle, so TODO: abstract out the request part of these functions
    base_req_url = 'http://api.urbandictionary.com/v0/define'

    res = requests.get(base_req_url, {'term': args})
    if not res.ok:
        self.send_message(message.channel, 'Error:', res.status_code,
                          '-', res.reason)
        return

    json = res.json()
    if json['result_type'] == 'no_results':
        self.send_message(message.channel, 'No results found.')
    else:
        entry = json['list'][0]
        definition = re.sub(r'\[(\w+)\]', '\\1', entry['definition'])

        reply = ''
        reply += definition[:1000].strip()
        if len(definition) > 1000:
            reply += '... (Definition truncated. '
            reply += 'See more at <{}>)'.format(entry['permalink'])
        reply += '\n\n{} :+1: :black_small_square: {} :-1:'.format(
            entry['thumbs_up'], entry['thumbs_down'])
        reply += '\n\nSee more results at <{}>'.format(
            re.sub(r'/\d*$', '', entry['permalink']))

        self.send_message(message.channel, reply)


_memos = {}


@Discordant.register_command('remember')
def _remember(self, args, message):
    global _memos

    key, *memo = args.split()
    if len(memo) == 0:
        if key in _memos:
            del _memos[key]
            self.send_message(message.channel, 'Forgot ' + key + '.')
        else:
            self.send_message(message.channel,
                              'Nothing given to remember.')
        return

    memo = args[len(key):].strip()
    _memos[key] = memo
    self.send_message(
        message.channel,
        "Remembered message '{}' for key '{}'.".format(memo, key))


@Discordant.register_command('recall')
def _recall(self, args, message):
    global _memos
    if args not in _memos:
        self.send_message(message.channel,
                          'Nothing currently remembered for ' + args + '.')
        return

    self.send_message(message.channel, _memos[args])
