from .discordant import Discordant
from discord import Embed
from datetime import datetime, timezone
from html import unescape
import re
import requests
from functools import partial
import asyncio


async def perform_async(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


@Discordant.register_handler(r'^ping$', re.I)
async def _ping(self, match, message):
    await self.send_message(message.channel,
                            message.content.replace('i', 'o')
                                           .replace('I', 'O'))


@Discordant.register_handler(r'\bayy+$', re.I)
async def _ayy_lmao(self, match, message):
    await self.send_message(message.channel, 'lmao')


@Discordant.register_command('youtube')
async def _youtube_search(self, args, message):
    base_req_url = 'https://www.googleapis.com/youtube/v3/search'
    req_args = {
        'key': self.config.get('API-Keys', 'youtube'),
        'part': 'snippet',
        'type': 'video',
        'maxResults': 1,
        'q': args
    }

    res = await perform_async(requests.get, base_req_url, req_args)
    if not res.ok:
        return await self.send_message(message.channel, f'Error: {res.status_code} - {res.reason}')

    json = res.json()
    if json['pageInfo']['totalResults'] == 0:
        await self.send_message(message.channel, 'No results found.')
    else:
        await self.send_message(message.channel, 'https://youtu.be/' +
                                json['items'][0]['id']['videoId'])


@Discordant.register_command('urban')
async def _urban_dictionary_search(self, args, message):
    base_req_url = 'http://api.urbandictionary.com/v0/define'

    res = await perform_async(requests.get, base_req_url, {'term': args})
    if not res.ok:
        return await self.send_message(message.channel, f'Error: {res.status_code} - {res.reason}')

    json = res.json()
    if json['result_type'] == 'no_results':
        await self.send_message(message.channel, 'No results found.')
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

        await self.send_message(message.channel, reply)


@Discordant.register_command('hn')
async def _hacker_news_summary(self, args: str, message):
    args = args.strip().lower()
    accepted_args = {'top', 'new', 'best', 'ask', 'show'}
    story_type = args if args in accepted_args else "top"
    story_type_url = f'https://hacker-news.firebaseio.com/v0/{story_type}stories.json'

    res = await perform_async(requests.get, story_type_url)
    if not res.ok:
        return await self.send_message(message.channel, f'Error: {res.status_code} - {res.reason}')

    story_list = res.json()[:1]
    done, _ = await asyncio.wait([
        perform_async(requests.get, f'https://hacker-news.firebaseio.com/v0/item/{id}.json')
        for id in story_list
    ])
    done = list(filter(lambda res: res.ok, map(lambda task: task.result(), done)))
    if len(done) == 0:
        return await self.send_message(message.channel, 'Failed to load any stories')

    story_json = list(map(lambda res: res.json(), done))[0]
    embed = Embed(
        title=story_json['title'],
        url=story_json['url'] if 'url' in story_json else f'https://news.ycombinator.com/item?id={story_json["id"]}',
        description='' if 'url' in story_json else unescape(
            re.sub(r'<[^>]+>', '', _sub_all(story_json['text']))
        ),
        timestamp=datetime.fromtimestamp(story_json['time'], tz=timezone.utc),
        type='rich'
    ).add_field(
        name='Score',
        value=f'{story_json["score"]} points',
        inline=True
    ).add_field(
        name='Comments',
        value=f'{story_json["descendants"]} ([view on HN](https://news.ycombinator.com/item?id={story_json["id"]}))',
        inline=True
    ).set_footer(
        text=story_json["by"],
        icon_url='https://news.ycombinator.com/y18.gif'
    )
    await self.send_message(message.channel, content=f'{story_type.capitalize()} story on Hacker News', embed=embed)


def _sub_all(string: str):
    replacements = {
        '<p>': '\n',
        '</?i>': '_',
        '</?b>': '*',
        '</?code>': '`'
    }
    for regex, replacement in replacements.items():
        string = re.sub(regex, replacement, string)
    return string
