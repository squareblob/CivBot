import datetime
import json
import math
import re
from operator import itemgetter

import aiohttp
import async_timeout
import discord
import nbtlib
from bs4 import BeautifulSoup
from discord.ext import commands

from cogs.ImageMeme import download_file


async def get_url(url, timeout=10):
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(timeout):
            async with session.get(url) as response:
                return await response.text()


async def get_account_info_from_web(ign):
    head_url = 'https://minotar.net/avatar/%s.png' % ign
    # namemc = await get_url('https://namemc.com/profile/' + ign)

    # first mcstats url: main page (top 10 servers)
    mcstats_url = 'https://minecraft-statistic.net/en/player/%s.html' % ign
    mcstats_1_html = await get_url(mcstats_url)
    soup1 = BeautifulSoup(mcstats_1_html, 'html.parser')
    servers = extract_mcstats_servers(soup1)

    # oldest to newest: tuple(name, datetime or None)
    names = [(
        t.span.text,
        parse_mcstats_name_change_time(t.next_sibling.next_sibling.span.text)
        ) for t in soup1.find_all(class_='text-right') if t.span]

    if not len(names): names = [(ign, None)]

    # second  mcstats url: remaining servers
    # BROKEN: apparently you need to pass the correct cookie
    # mcstats_2_json = await get_url('https://minecraft-statistic.net/en/player/servers_ajax/' + ign)
    # mcstats_2_jsonobj = json.loads(mcstats_2_raw)
    # mcstats_2_html = mcstats_2_json['html']
    # soup2 = BeautifulSoup(mcstats_2_html, 'html.parser')
    # servers += extract_mcstats_servers(soup2)

    l = locals()
    return {k: l[k] for k in 'mcstats_url head_url names servers'.split()}


def parse_mcstats_name_change_time(s):
    if s == 'Name at registration': return None
    return datetime.datetime.strptime(s, "%Y.%m.%d %H:%M")


def extract_mcstats_servers(soup):
    """Returns a list of tuples containing: address, motd, timestamp of last visit, hours played on server"""
    return [(
        t.find_all(class_='copy-ip')[0]['data-clipboard-text']
            .replace(':25565', ''),
        t.find_all(class_='lv-title')[0].text,
        t['data-last-visit'],
        int(t['data-total-time']) // 60
        ) for t in soup.find_all(class_='servers-list-item')
        if t.has_attr('data-last-visit')]


class MiscUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def whois(self, ctx, *, content):
        # todo : this command is probably broken

        """Get info about that IGN from namemc.com and minecraft-statistic.net"""
        ign = discord.utils.escape_mentions(content.split(' ')[0])
        info = await get_account_info_from_web(ign)
        num_servers = len(info['servers'])
        if num_servers == 10: num_servers = '9+'
        if info['names'][-1][1]:
            delta = datetime.datetime.now() - info['names'][-1][1]
            delta = str(delta).split(':')[0] + 'h'
            datestr = info['names'][-1][1].strftime("%b %d %Y %H:%M")
            name_age = '%s ago (%s)' % (delta, datestr)
        else:
            name_age = 'never'
        joined_names = ' '.join(sorted(set(
            name for (name, date) in info['names'][:-1])))
        joined_names = joined_names or 'None'
        joined_servers = ', '.join(
            '%s (%sh)' % (ip, hours)
            for (ip, motd, last_seen, hours) in info['servers'])
        joined_servers = joined_servers or 'None'

        ign_clean = ign.replace('_', '\\_')
        joined_names_clean = joined_names.replace('_', '\\_')
        joined_servers_clean = joined_servers.replace('_', '\\_')
        text = '''
    **{ign_clean}**
    Last name change: {name_age}
    Past names: {joined_names_clean}
    Seen on {num_servers} servers: {joined_servers_clean}
    Sources: <{info[mcstats_url]}> <https://namemc.com/profile/{ign}> {info[head_url]}
    '''.format(**locals()).strip()
        await ctx.channel.send(text)

    @commands.command(pass_context=True)
    async def whereis(self, ctx, x, z, fromRelay=False):
        """Gives nearby markers from CCmap data"""
        if re.match("[+-]?\d", x) and re.match("[+-]?\d", z):
            distances = {}
            # todo : download from github
            with open("resources/MiscUtilities/settlements.civmap.json") as f:
                ccmap = json.load(f)

            for k in ccmap['features']:
                distance = int(math.sqrt((int(x) - int(k['x'])) ** 2 + (int(z) - int(k['z'])) ** 2))
                distances[k['id']] = distance
            distances = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}

            out = str(
                "<https://ccmap.github.io/#c=" + str(int(x)) + "," + str(int(z)) + "," + "r400>") + " ```asciidoc\n"
            for d in range(0, 14 if not fromRelay else 4):
                ind = list(map(itemgetter('id'), ccmap['features'])).index(list(distances)[d])
                rad = math.atan2(ccmap['features'][ind]['z'] - int(z), ccmap['features'][ind]['x'] - int(x))

                dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW',
                        'NNW']
                ix = round(math.degrees(rad) / (360. / len(dirs)))
                xtra = ""
                if "Zoom Visibility" in ccmap['features'][ind]:
                    if ccmap['features'][ind]["Zoom Visibility"] <= 2:
                        xtra = " ::"

                out += str(distances[list(distances)[d]]).rjust(4, " ") + "  blocks " + (dirs[ix % len(dirs)]).rjust(5,
                                                                                                                     " ") + "  " + \
                       ccmap['features'][ind]['name'] + xtra + "\n"
            if not fromRelay:
                await ctx.channel.send((str(out) + "```"))
            else:
                await ctx.channel.send((str(out).replace("```asciidoc", "").replace("::", "✪")))

    async def getschematic(self, ctx, schematicfile):
        await download_file(schematicfile.url, 'resources/test.schematic')
        nbt_file = nbtlib.load('resources/test.schematic')
        blocks = nbt_file['Schematic']['Blocks']

        async with aiohttp.ClientSession() as session:
            async with session.get('https://minecraft-ids.grahamedgecombe.com/items.json') as r:
                if r.status == 200:
                    sch = await r.json(content_type='text/plain')

        # really makes you think
        block_ids = []
        block_counts = []
        for x in set(blocks):
            block_ids.append(str(x).upper())
            block_counts.append(str(blocks).replace("B; ", "").split(", ").count(str(x).upper()))

        block_counts, block_ids = zip(*sorted(zip(block_counts, block_ids), reverse=True))

        output = "```\n"
        for i in range(0, len(block_ids)):
            b_name = "None"
            b_id_clean = int(re.sub("[^0-9]", "", block_ids[i]))
            item = next((item for item in sch if item['type'] == b_id_clean), None)
            if item is not None:
                b_name = item['name']
            if b_name.lower() == "air":
                continue
            if '-' in block_ids[i]:
                b_name = "???"
            output += b_name.rjust(30, " ") + "  " + str(block_counts[i]).ljust(2, " ") + "\n"

        await ctx.channel.send(output + "```")


def setup(bot):
    bot.add_cog(MiscUtilities(bot))
