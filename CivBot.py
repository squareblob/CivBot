import asyncio
import configparser
import datetime
import functools
import json
import math
import os
import random
from discord.ext import menus
from random import randint
import re
import time
import uuid
from _operator import itemgetter
import io
import yaml
from os import path

import pycountry
import requests

import aiofiles
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import nbtlib
from PIL import Image, ImageDraw, ImageFont, ImageOps
from mcuuid.api import GetPlayerData
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle as pickle1

from cogs.ImageMeme import download_file
from perchance import perchance_gen, perchance_parse

prefix = "%"

# cut down on spam: don't respond if last response was recent
last_times = {}

def clean_text_for_discord(text):
    text = text.replace("_", "\_")
    text = text.replace("*", "\*")
    text = text.replace("~~", "\~~")
    return text


def get_response():
    wordlist = ["crying",
                "shaking",
                "oscillating",
                "deleting vault group",
                "yelling",
                "screaming",
                "vibrating",
                "overdosing",
                "collapsing",
                "writhing",
                "hyperventilating"]

    random.shuffle(wordlist)
    length = random.randrange(1, 5)
    words = []
    for i in range(length):
        words.append(wordlist.pop())
    if length == 1:
        response = words[0]
    elif length == 2 and random.random() > 0.1:
        response = " and ".join(words)
    else:
        response = ", ".join(words)
    return response


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


async def get_url(url, timeout=10):
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(timeout):
            async with session.get(url) as response:
                return await response.text()


def wiardify(text):
    vowels = "aeiouy"
    consonants = "bcdfghjklmnpqrstvwxz"
    t2 = ""
    for i in range(len(text)):
        try:
            if text[i-1].lower() in vowels and text[i+1].lower() in vowels and text[i].lower() in consonants:
                pass
            else:
                t2 += text[i]
        except:
            t2 += text[i]
    return t2

def unwiardify(text):
    vowels = "aeiouy"
    consonants = "bcdfghjklmnpqrstvwxz"
    t2 = ""
    for i in range(len(text)):
        try:
            if text[i].lower() in vowels and text[i+1].lower() in vowels:
                if random.random()>0.5:
                    t2 += text[i]
                    t2 += random.choice(consonants)
                else:
                    t2 += text[i]
            else:
                t2 += text[i]
        except:
            t2 += text[i]
    return t2


bot = commands.Bot(command_prefix=prefix, description="CivBot", help_command=None);


@bot.command(pass_context=True)
async def oracle(ctx):
    """Gives a oracle response"""
    wordlist = ["That is definitely not canon and may in fact be illegal",
                "Roleplay Detected",
                "this is the sort of thing said by the sort of people squareblob sort of vowed to sort of destroy",
                "Good luck you little bingus",
                "you can't create an idea, idiot",
                "Supercringe giganormie"]
    await ctx.channel.send(random.choice(wordlist))


@bot.command(pass_context=True)
async def thraldrek(ctx):
    """Gives a thraldrek response"""
    country_name = random.choice(list(pycountry.countries)).name
    if random.randint(0, 200) == 1:
        country_name = "Thrain Family Forest"
    wordlist = ["Isn't " + ctx.author.name + " from " + country_name]
    await ctx.channel.send(random.choice(wordlist))


@bot.command(pass_context=True)
async def topher(ctx):
    """Gives a topher response"""
    # todo get most recent 10 messages, and do not reuse.
    lines = open('resources/wordlist_topher.txt').read().splitlines()
    message = str(random.choice(lines))
    message = message.replace('%user', ctx.author.name).replace('\\n', '\n')
    if '%randemoji' in message:
        emojis = ctx.guild.emojis
        if len(emojis) == 0:
            message = "Topher says : add a custom emoji"
        else:
            emoji = random.choice(emojis)
            message = message.replace('%randemoji', ":" + emoji.name + ":")
    if '%randuser' in message:
        user = random.choice(ctx.guild.members)
        message = message.replace('%randuser', user.name)
    await ctx.channel.send(message)
    if random.randint(0, 3) == 3:
        await ctx.channel.send(file=discord.File('resources/topher.gif'))


@bot.command(pass_context=True)
async def freestyle(ctx):
    await ctx.channel.send(file=discord.File('resources/topher.gif'))

@bot.event
async def on_message(ctx):
    try:
        if ctx.author.id == bot.user.id: return  # ignore self
        else:
            match_relay_chat_command = re.match("(?:`\[(?:\S+)\]` )*\[(?:\S+)\] ((%(?:\S+))(?: .+)*)", ctx.content)
            if len(ctx.content) != 0 and prefix == ctx.content[0]:
                await bot.process_commands(ctx)
            elif match_relay_chat_command:
                ctx.content = match_relay_chat_command.group(1).strip()
                if match_relay_chat_command.group(2) == "%whereis":
                    coords = re.match("%whereis ((?:[+-]?\d)+)[ ,]((?:[+-]?\d)+)", ctx.content)
                    await whereis(ctx, coords.group(1), coords.group(2), True)
                elif match_relay_chat_command.group(2) == "%drama": # set temporarily as somehow broken
                    await drama(ctx)
                else:
                    print(ctx.content)
                    await bot.process_commands(ctx)
            else:  # regular chat message
                lower_content = ctx.content.lower()
                if 'delusional' in lower_content:
                    await ctx.channel.send("Edit CivWiki <https://civclassic.miraheze.org/wiki/CivWiki:Editing_Guide>")
                if 'lusitanian' in lower_content:
                    await ctx.channel.send(file=discord.File('resources/ImageMemeTemplates/Lusitan.png'))
                if 'linux' in lower_content and not 'gnu' in lower_content and 60 > time.time() - last_times.get('gnu_linux', 0):
                    last_times['gnu_linux'] = time.time()
                    await ctx.channel.send(gnu_linux)
                message = ""
                pages = list(set(re.findall("(\[\[ *[^\]]+ *\]\])", ctx.content) + re.findall("(\{\{ *[^\]]+ *\}\})", ctx.content)))
                for page in pages:
                    message = 'https://civclassic.miraheze.org/wiki/'
                    if re.match("\{\{ *([^\]]+) *\}\}", page):
                        message += "Template:"
                    page = list(set(re.findall("\[\[ *([^\]]+) *\]\]", ctx.content) + re.findall("\{\{ *([^\]]+) *\}\}", ctx.content)))[0]
                    message += page.replace(" ", "_") + "\n"
                if len(pages) > 0:
                    await ctx.channel.send(message)
            if len(ctx.attachments) != 0:
                for x in ctx.attachments:
                    if os.path.splitext(x.filename)[1] == ".schematic":
                        await getschematic(ctx, x)
    except AttributeError:
        print("From " + str (ctx.author) + ": " + ctx.content)


async def getschematic(ctx, schematicfile):
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


@bot.command(pass_context=True)
async def respond(ctx):
    """Gives a Civ response"""
    await ctx.channel.send(get_response())


@bot.command(pass_context=True)
async def invite(ctx):
    """CivBot invite"""
    await ctx.channel.send("https://discordapp.com/api/oauth2/authorize?client_id=614086832245964808&permissions=0&scope=bot")


@bot.group()
async def chart(ctx):
    '''Create x,y charts with Minecraft faces'''
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid command passed...\nOptions include `view`,`edit`,`create`')


def draw_chart(chart_data, chart_code):
    x_axis = chart_data[str(chart_code)]["x_axis"]
    y_axis = chart_data[str(chart_code)]["y_axis"]

    # DRAW TEXT
    background = Image.open("resources/grid2500.png")
    font = ImageFont.truetype("resources/fonts/NotoSans-Bold.ttf", 128)
    img_txt = Image.new('L', font.getsize(y_axis))
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((0, 0), y_axis, font=font, fill=255)
    t = img_txt.rotate(90, expand=1)
    background.paste(ImageOps.colorize(t, (0, 0, 0), (0, 0, 0)),
                     (-10, int((background.height - font.getsize(y_axis)[0]) / 2)), t)
    draw = ImageDraw.Draw(background)
    draw.text((int((background.width - font.getsize(x_axis)[0]) / 2), 2320), x_axis, (0, 0, 0), font=font)

    # DRAW faces
    for player_name in chart_data[str(chart_code)]['chart_data'].keys():
        x_cord_total = 0
        y_cord_total = 0
        for discord_id in chart_data[str(chart_code)]['chart_data'][str(player_name)]:
            x_cord_total += float(chart_data[str(chart_code)]['chart_data'][str(player_name)][str(discord_id)]["x_coord"])
            y_cord_total += float(chart_data[str(chart_code)]['chart_data'][str(player_name)][str(discord_id)]["y_coord"])

        total = len(chart_data[str(chart_code)]['chart_data'][str(player_name)])
        coords = [x_cord_total/total, y_cord_total/total]
        face_width = 120
        fixed_coords = [int((coords[0] / 100) * background.width - (face_width / 2)),
                        int((background.height - ((coords[1] / 100) * background.height)) - (face_width / 2))]
        if GetPlayerData(player_name).valid:
            if path.exists("resources/playerheads/" + str(player_name) + ".png"):
                pass
            else:
                r = requests.get(
                    "https://mc-heads.net/avatar/" + GetPlayerData(player_name).uuid + "/" + str(face_width) + ".png")
                with open("resources/playerheads/" + str(player_name) + ".png", 'wb') as f:
                    f.write(r.content)
            playertopaste = Image.open("resources/playerheads/" + player_name + ".png")
            background.paste(playertopaste, tuple(fixed_coords))
    background.save('resources/output.png', "PNG")


@chart.command()
async def view(ctx, chart_code):
    '''Views a saved chart'''
    with open("resources/chart_creator.txt") as json_file:
        chart_data = json.load(json_file)
    if str(chart_code) in chart_data.keys():
        params = functools.partial(draw_chart, chart_data, chart_code)
        run_draw = await bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))


@chart.command()
async def edit(ctx, chart_code, playername, xpos, ypos):
    '''Edits a chart with given chart code, Minecraft username, x coord and y coord.'''
    with open("resources/chart_creator.txt") as json_file:
        chart_data = json.load(json_file)
    try:
        if float(xpos) > 100 or float(xpos) < 0 or float(ypos) > 100 or float(ypos) < 0:
            await ctx.send("input must range between 0 to 100")
            return
    except ValueError:
        await ctx.send("Must be number")
        return
    if not GetPlayerData(playername).valid:
        await ctx.send("this is not a valid playername")
        return
    if str(chart_code) in chart_data.keys():
        if not str(playername) in chart_data[chart_code]['chart_data'].keys():
            chart_data[chart_code]['chart_data'][str(playername)] = {}

        chart_data[chart_code]['chart_data'][str(playername)][str(ctx.author.id)] = {
            "x_coord": str(xpos),
            "y_coord": str(ypos)
        }

        with open("resources/chart_creator.txt", "w") as json_file:
            json.dump(chart_data, json_file)

        # optional : show chart after posting
        params = functools.partial(draw_chart, chart_data, chart_code)
        run_draw = await bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))
    else:
        await ctx.send("chart not found")
    # make create chart method, view


@chart.command()
async def create(ctx, chart_name):
    '''Creates a chart with given chart name'''
    with open("resources/chart_creator.txt") as json_file:
        chart_data = json.load(json_file)

    await ctx.send('Name X-axis:')
    def pred(m):
        return m.author == ctx.author and m.channel == ctx.channel

    x_axis = await bot.wait_for('message', check=pred, timeout=60.0)
    await ctx.send('Name Y-axis:')
    y_axis = await bot.wait_for('message', check=pred, timeout=60.0)

    if len(x_axis.content) > 20 or len(y_axis.content) > 20:
        await ctx.send('Both X-axis and Y-axis must be under 20')
        return

    while True:
        chart_id = str(uuid.uuid4())[:6]
        if str(chart_id) not in chart_data.keys():
            break
    chart_data[str(chart_id)] = {}
    chart_data[str(chart_id)]['chart_name'] = str(chart_name)
    chart_data[str(chart_id)]['chart_owner'] = ctx.author.id
    chart_data[str(chart_id)]['x_axis'] = str(x_axis.content)
    chart_data[str(chart_id)]['y_axis'] = str(y_axis.content)
    chart_data[str(chart_id)]['chart_data'] = {}

    with open("resources/chart_creator.txt", "w") as json_file:
        json.dump(chart_data, json_file)
    await ctx.send(':white_check_mark: Chart created. Chart can be accessed with the code ' + str(chart_id))


@bot.group()
async def civdiscord(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid command passed...')


def getpath(nested_dict, value, prepath=()):
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == value:
            return path
        elif hasattr(v, 'items'): # v is a dict
            p = getpath(v, value, path) # recursive call
            if p is not None:
                return p


@civdiscord.command()
async def search(ctx, content):
    with open(discord_loc) as json_file:
        discord_data = json.load(json_file)
    return_paths = []
    matches = []
    keys = []

    for key in discord_data:
        # fix
        if 'current_name' in discord_data[key].keys():
            if len(content) > 4:
                match = fuzz.token_set_ratio(content, discord_data[key]['current_name'])
            else:
                match = fuzz.ratio(content, discord_data[key]['current_name'])
        if 'nickname' in discord_data[key].keys():
            test, match = process.extractOne(content, discord_data[key]['nickname'])
            # for x in discord_data[key]['nickname']:
            #     if len(content) > 4:
            #         match = fuzz.token_set_ratio(content, x)
            #     else:
            #         match = fuzz.ratio(content, x)
        if match > 50:
            if 'valid_invites' in discord_data[key].keys() and len(discord_data[key]['valid_invites']) > 0:
                keys.append(key)
                matches.append(match)
    if len(matches) > 0:
        matches, keys = zip(*sorted(zip(matches, keys), reverse=True))
        resp = "Only showing top 4 matches\n" if len(matches) > 4 else ""
        stop = 4 if len(matches) >= 4 else len(matches)
        for i in range(0, stop):
            rating = 0
            stars = None
            if 'rating' in discord_data[keys[i]].keys():
                for l in discord_data[keys[i]]["rating"].keys():
                    rating += discord_data[keys[i]]["rating"][l]
                rating = rating/len(discord_data[keys[i]]["rating"])
                stars = ("".join([":star:" for x in range(0, int(rating))]) + ('+' if rating > int(rating)+.4 else ""))

            resp += discord_data[keys[i]]['valid_invites'][0] + (" " + stars if stars is not None else "") + "\n"

        await ctx.send(resp)
    else:
        await ctx.send("No matches could be found")


async def checkinvite(ctx, content):
    try:
        invite = await bot.fetch_invite(content)
        if invite is not None:
            with open(discord_loc) as json_file:
                discord_data = json.load(json_file)
            return discord_data, invite
    except discord.NotFound:
        await ctx.send("This is not a valid invite")
        return None


@civdiscord.command()
async def add(ctx, content):
    discord_data, invite = await checkinvite(ctx, content)
    if discord_data is not None:
        inv_id = str(invite.guild.id)
        if inv_id not in discord_data.keys():
            discord_data[inv_id] = {}
            discord_data[inv_id]['valid_invites'] = [str(content)]
            discord_data[inv_id]['invalid_invites'] = []
            discord_data[inv_id]['current_name'] = str(invite.guild.name)
            discord_data[inv_id]['approximate_member_count'] = str(invite.approximate_member_count)
            with open(discord_loc, 'w') as outfile:
                json.dump(discord_data, outfile)
            await ctx.send("Added a new guild")
        else:
            if str(content) in discord_data[inv_id]['valid_invites']:
                await ctx.send("This invite code has already been submitted")
            else:
                discord_data[inv_id]['valid_invites'].append(str(content))
                with open(discord_loc, 'w') as outfile:
                    json.dump(discord_data, outfile)
                await ctx.send("Invite code was successfully added")


@civdiscord.command()
async def nick(ctx, inv_code, name):
    '''Adds a nickname to discord server entry'''
    try:
        discord_data, invite = await checkinvite(ctx, inv_code)
        print(inv_code)
        if discord_data is not None:
            inv_id = str(invite.guild.id)
            if inv_id not in discord_data.keys():
                ctx.send("This invite id must first be submitted. Use %civdiscord add INVITE")
            else:
                if 'nickname' not in discord_data[inv_id].keys():
                    discord_data[inv_id]['nickname'] = []

                if name in discord_data[inv_id]['nickname']:
                    await ctx.send(":x:Nickname has already been added")
                else:
                    discord_data[inv_id]['nickname'].append(name)
                    with open(discord_loc, 'w') as outfile:
                        json.dump(discord_data, outfile)
                    await ctx.send("Nickname was added")
    except FileNotFoundError as e:
        await ctx.send("Nickname must be in format \"invite_code nickname\"")


@civdiscord.command()
async def rate(ctx,  inv_code, rating):
    '''Rates a discord server'''
    try:
        discord_data, invite = await checkinvite(ctx, inv_code)
        if discord_data is not None:
            inv_id = str(invite.guild.id)
            if inv_id not in discord_data.keys():
                ctx.send("This invite id must first be submitted. Use %civdiscord add INVITE")
            else:
                if 'rating' not in discord_data[inv_id].keys():
                    discord_data[inv_id]['rating'] = {}

                old_rating = None
                if str(ctx.author.id) in discord_data[inv_id]['rating'].keys():
                    old_rating = int(discord_data[inv_id]['rating'][str(ctx.author.id)])
                    print("old-rating="+ str(old_rating))
                if rating.isdigit() and 1 <= int(rating) <= 5:
                    rating = int(rating)
                    msg = ""
                    discord_data[inv_id]['rating'][str(ctx.author.id)] = rating
                    if old_rating is not None:
                        msg += "Old rating :" + ("".join([":star:" for x in range(0, int(old_rating))]) + ('+' if old_rating > int(old_rating)+.4 else "")) + "\n"
                    msg += "Rating :" + ("".join([":star:" for x in range(0, int(rating))]) + ('+' if rating > int(rating)+.4 else "")) + "\n"
                    with open(discord_loc, 'w') as outfile:
                        json.dump(discord_data, outfile)
                    await ctx.send(msg)
                else:
                    await ctx.send("Rating must be integer between 1 and 5 stars")
    except FileNotFoundError:
        await ctx.send("Nickname must be in format \"invite_code nickname\". Invite code must be valid")


@bot.command(pass_context=True)
async def generateplugin(ctx, content='1'):
    """Generates a civ server plugin"""
    with open('resources/Techs.txt') as f:
        plugin_base = [line.rstrip().replace(" ","_") for line in f]
    prefix = ["Better", "Civ", "Realistic", "Old", "Simple", "Meme", "Add", "Quirky"]
    base = ["Biomes", "Bastion", "Item", "Citadel", "Enchanting", "Combat", "Brewery", "Border", "Teleports", "Instant_Death", "Block_Puzzles", "Information_Overload", "Disinformation", "Gravity", "Bullet_Hell", "Brawl", "Disease", "Crop"]
    plugin_base = plugin_base + base
    suffix = ["Core", "Alert", "-spawn", "Colors", "Layer", "Exchange", "Mod", "Stick", "Mana", "Spy", "Plus", "Manager","Fix","Alts","Tweaks","Tools","fuscator","Pearl","limits","Ore","egg", "Shards", "Cull", "Contraptions", "PvP", "Bank"]

    num = 1
    response = ""
    if content.isdigit():
        if int(content) <= 4:
            num = int(content)
        else:
            num = 4
    for x in range(0, num):
        gen_prefix = ""
        gen_suffix = ""
        if random.randrange(10) >= 0:
            gen_suffix = random.choice(suffix)
        if (random.randrange(10) >= 8 and gen_prefix == "") or random.randrange(10) >= 6:
            gen_prefix = random.choice(prefix)
        response += gen_prefix + random.choice(plugin_base) + gen_suffix + "\n"
    await ctx.channel.send(response)


# @bot.command(pass_context=True)
# async def dox(ctx, content):
#     """'Doxes' a player"""
#     fake = Faker()
#     await ctx.channel.send("...Scanning information for " + discord.utils.escape_mentions(content) + "'s minecraft alts...")
#     await ctx.channel.trigger_typing()
#     await asyncio.sleep(3)
#     if random.randrange(0, 6) == 5:
#         try:
#             await ctx.guild.kick(ctx.message.author, reason="Dox attempt")
#             await ctx.channel.send("User was kicked from the server for attempted dox")
#         except discord.Forbidden:
#             pass
#     else:
#         Faker.seed(content)
#         await ctx.channel.send(":white_check_mark: " + fake.name())

@bot.command(pass_context=True)
async def pplocate(ctx, *, content):
    """Locates a players pearl"""
    with open('resources/pearl locations.txt', 'r') as file:
        locations = json.load(file)
    if content.lower() in locations:
        await ctx.channel.send(locations[content])
    else:
        await ctx.channel.send("**" + clean_text_for_discord(content) + "**'s pearl could not be located")


@bot.command(pass_context=True, brief = "Frees a players pearl")
async def ppfree(ctx, *, content):
    """`ppfree <playername>`"""
    with open('resources/pearl locations.txt', 'r') as file:
        locations = json.load(file)
    if content.lower() in locations:
        await ctx.channel.send("You freed **" + clean_text_for_discord(content) + "**")
        del locations[content.lower()]
        with open('resources/pearl locations.txt', 'w') as file:
            json.dump(locations, file)


@bot.command(pass_context=True)
async def wiard(ctx, *, content):
    """wiardifies a message"""
    await ctx.channel.send(wiardify(content))
    
@bot.command(pass_context=True)
async def unwiard(ctx, *, content):
    """unwiardifies a message"""
    await ctx.channel.send(unwiardify(content))

perchance_civ_classic = perchance_parse(open('resources/perchance.txt').read())
# perchance_fun_fact = perchance_parse(open('resources/perchance_funfact.txt').read())

@bot.command(pass_context=True)
async def drama(ctx):
    """Generates CivClassic drama"""
    await ctx.channel.send(perchance_gen(perchance_civ_classic))

# @bot.command(pass_context=True)
# async def funfact(ctx):
#     """Generates a CivClassic funfact"""
#     await ctx.channel.send(perchance_gen(perchance_fun_fact))

@bot.command(pass_context=True)
async def pickle(ctx, content):
    """Pickles a player"""
    with open('resources/Food adjectives.txt') as f:
        lines = f.read().splitlines()
    adjs = []
    for a in lines:
        if a[0].casefold() == content[0].casefold():
            adjs.append(a)
    if content.casefold() == "pirater":
        adjs = ["pickled"]
    if len(adjs) > 0:
        await ctx.channel.send(random.choice(adjs).capitalize() + " " + clean_text_for_discord(content))

@bot.command(pass_context=True)
async def whereis(ctx, x, z, fromRelay=False):
    """Gives nearby markers from CCmap data"""
    if re.match("[+-]?\d", x) and re.match("[+-]?\d", z):
        distances = {}
        with open("resources/settlements.civmap.json") as f:
            ccmap = json.load(f)

        for k in ccmap['features']:
            distance = int(math.sqrt((int(x) - int(k['x'])) ** 2 + (int(z) - int(k['z'])) ** 2))
            distances[k['id']] = distance
        distances = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}

        out = str("<https://ccmap.github.io/#c="+ str(int(x)) + "," + str(int(z)) + "," + "r400>") + " ```asciidoc\n"
        for d in range(0, 14 if not fromRelay else 4):
            ind = list(map(itemgetter('id'), ccmap['features'])).index(list(distances)[d])
            rad = math.atan2(ccmap['features'][ind]['z'] - int(z), ccmap['features'][ind]['x'] - int(x))

            dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
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
            await ctx.channel.send((str(out).replace("```asciidoc", "").replace("::","✪")))


@bot.command(pass_context=True)
async def generatename(ctx):
    await ctx.channel.send("Random Minecraft name generator is creating your username...")
    await ctx.channel.trigger_typing()
    await asyncio.sleep(3)

    if random.randint(0, 20) != 1:
        await ctx.channel.send("...please be patient, our state of the art algorithms are still processing your request...")
        await ctx.channel.trigger_typing()
        await asyncio.sleep(random.randint(5, 7))

        if random.randint(0, 3) == 3:
            await ctx.channel.send("...your request was computationally intensive and requires additional processing...")
            await ctx.channel.trigger_typing()
            await asyncio.sleep(random.randint(7, 12))

    await ctx.channel.send("Your username is **minemaster" + str(randint(100, 999)) + "**")


@bot.command(pass_context=True)
async def whois(ctx, *, content):
    """Get info about that IGN from namemc.com and minecraft-statistic.net"""
    ign = content.split(' ')[0]
    info = await get_account_info_from_web(ign)
    num_servers = len(info['servers'])
    if num_servers == 10: num_servers = '9+'
    if info['names'][-1][1]:
        delta = datetime.datetime.now() - info['names'][-1][1]
        delta = str(delta).split(':')[0] + 'h'
        datestr = info['names'][-1][1].strftime("%b %d %Y %H:%M")
        name_age = '%s ago (%s)' % (delta, datestr)
    else: name_age = 'never'
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


gnu_linux = """
I'd just like to interject for a moment. What you're referring to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell utilities and vital system components comprising a full OS as defined by POSIX.

Many computer users run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called "Linux", and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.

There really is a Linux, and these people are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called "Linux" distributions are really distributions of GNU/Linux.
""".strip()


@bot.event
async def on_ready():
    print("connected to discord")
    print("In " + str(len(bot.guilds)) + " guilds")
    for guild in bot.guilds:
        print(guild.name)

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('reddit.com/r/civclassics'))

    with open('resources/VC_temp_storage.pickle', 'wb') as handle:
        pickle1.dump([], handle, protocol=pickle1.HIGHEST_PROTOCOL)


extensions = [
    "ImageMeme",
]

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_type = 'auth'
    config.read('config.ini')
    token = config.get(config_type, 'token')
    discord_loc = config.get(config_type, 'discord_loc')

    for extension in extensions:
        bot.load_extension(f"cogs.{extension}")

    while True:
        try:
            bot.run(token)
        except Exception as e:
            print("Error", e)
        print("Waiting until restart")
        time.sleep(20)
