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


def _split_args(args):
    return list(filter(lambda arg: len(arg) > 0, args.split(' ')))


@Discordant.register_command('hn', arg_func=_split_args)
async def _hacker_news_summary(self, args, message):
    arg = args[0].strip().lower()
    accepted_args = {'top', 'new', 'best', 'ask', 'show'}
    story_type = arg if arg in accepted_args else "top"
    story_type_url = f'https://hacker-news.firebaseio.com/v0/{story_type}stories.json'

    res = await perform_async(requests.get, story_type_url)
    if not res.ok:
        return await self.send_message(message.channel, f'Error: {res.status_code} - {res.reason}')

    story_count = 1
    if len(args) == 1 and args[0].strip().isdecimal() or len(args) > 1 and args[1].strip().isdecimal():
        story_count = min(int(args[0 if len(args) == 1 else 1].strip()), 10)

    story_list = res.json()[:story_count]
    done, _ = await asyncio.wait([
        perform_async(requests.get, f'https://hacker-news.firebaseio.com/v0/item/{id}.json')
        for id in story_list
    ])
    done = list(filter(lambda res: res.ok, map(lambda task: task.result(), done)))
    if len(done) == 0:
        return await self.send_message(message.channel, 'Failed to load any stories')

    if story_count == 1:
        story_json = list(map(lambda res: res.json(), done))[0]
        embed = _create_single_story_embed(story_json)
        await self.send_message(message.channel, content=f'{story_type.capitalize()} story on Hacker News', embed=embed)
    else:
        story_list_json = list(map(lambda res: res.json(), done))
        embed = _create_story_list_embed(story_list_json, story_type)
        await self.send_message(message.channel, content=None, embed=embed)


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


def _create_single_story_embed(story_json):
    return Embed(
        title=story_json['title'],
        url=_get_hn_story_link(story_json),
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


def _create_story_list_embed(story_json_list, stories_type):
    embed = Embed(
        title=f'{len(story_json_list)} {stories_type.lower()} stories on Hacker News',
        description='',
        type='rich'
    )

    if stories_type.lower() == 'best':
        story_json_list.sort(key=lambda json: json['score'], reverse=True)
    for story_json in story_json_list:
        time_ago = datetime.now(tz=timezone.utc) - datetime.fromtimestamp(story_json['time'], tz=timezone.utc)
        if time_ago.days > 0:
            time_ago = f'{int(time_ago.days)} days ago'
        elif time_ago.total_seconds() > 60 * 60:
            time_ago = f'{int(time_ago.total_seconds() // (60 * 60))} hours ago'
        else:
            time_ago = f'{int(time_ago.total_seconds() // 60)} minutes ago'

        embed.add_field(
            name=story_json['title'],
            value=' | '.join([
                f'[link]({_get_hn_story_link(story_json)})',
                f'{story_json["score"]} points by {story_json["by"]} {time_ago}',
                f'{story_json["descendants"]} comments ([view on HN](https://news.ycombinator.com/item?id={story_json["id"]}))'
            ]),
            inline=False
        )
    return embed


def _get_hn_story_link(story_json):
    return story_json['url'] if 'url' in story_json else f'https://news.ycombinator.com/item?id={story_json["id"]}'
