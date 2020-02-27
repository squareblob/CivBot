import asyncio
import configparser
import datetime
import functools
import json
import math
import pprint
import random
import re
import string
import time
from _operator import itemgetter
from json import JSONDecodeError
import io

import requests

import aiofiles
import aiohttp
import async_timeout
from config import *
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
import nbtlib
from PIL import Image, ImageDraw, ImageFont, ImageOps
from discord.ext.commands import has_permissions
from faker import Faker
from mcuuid.api import GetPlayerData
import pickle as pickle1

prefix = "%"

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

def generate_pearl_image(pearled_player, pearled_by, now):
    random.seed(a=pearled_player.lower() + pearled_by.lower() + now, version=2)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    font = ImageFont.truetype("resources/Minecraftia.ttf", 24)
    font_italic = ImageFont.truetype("resources/Minecraft-Italic.otf", 30)
    im = Image.open("resources/Pearl_template.png")

    req_width = max(129 + font.getsize(pearled_player + "#" + code)[0] + 23, 129 + font.getsize(pearled_by)[0] + 40)

    if req_width > im.width:
        new_image = Image.new('RGB', (req_width, im.height))
        new_image.paste(im, (0, 0))
        crop = im.crop((453, 0, 456, 412))
        end_sliver = im.crop((461, 0, 466, 412))
        for i in range(im.width - 7, req_width, 3):
            new_image.paste(crop, (i, 0))
        new_image.paste(end_sliver, (new_image.width - 5, 0))
        im = new_image

    draw = ImageDraw.Draw(im)
    colors = [[(85, 255, 255), (255, 255, 255), (170, 170, 170), (85, 85, 85)],
              [(21, 63, 63), (63, 63, 63), (42, 42, 42), (21, 21, 21)]]

    for i in reversed(range(0, 2)):
        offset = -i * 3
        # Top title; Endcode; Player; Seed; Date; Killed by
        draw.text((10 - offset, 8 - offset), pearled_player, font=font_italic, fill=colors[i][0])
        draw.text((10 + font.getsize(pearled_player)[0] + 12 + 2 - offset, 2 - offset), "(#0368)", font=font,
                  fill=colors[i][1])
        draw.text((129 - offset, 68 - offset), pearled_player, font=font, fill=colors[i][2])
        draw.text((129 + font.getsize(pearled_player)[0] + 12 - offset, 68 - offset), "#" + code, font=font,
                  fill=colors[i][3])
        draw.text((165 - offset, 128 - offset), now, font=font, fill=colors[i][2])
        draw.text((156 - offset, 158 - offset), pearled_by, font=font, fill=colors[i][2])
    im.save('resources/output.png', "PNG")

async def download_file(url, outurl):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(outurl, mode='wb')
                await f.write(await resp.read())
                await f.close()

async def find_a_posted_image(ctx):
    if len(ctx.message.attachments) == 0:
        check_above = await ctx.message.channel.history(limit=14).flatten()
        for o in check_above:
            if len(o.attachments) != 0:
                await download_file(o.attachments[0].url, 'resources/output.png')
                return True
    else:
        await download_file(ctx.message.attachments[0].url, 'resources/output.png')
        return True
    return

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
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
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

def getmotd():
    random.seed(datetime.datetime.today().strftime('%m/%d/%Y'))
    return random.choice(["olive",
                          "olives",
                          "kalamata olive",
                          "kalamata olives",
                          "sliced kalamata olives",
                          "sliced kalamata olives in brine",
                          "pre-owned sliced kalamata olives in brine",
                          "i think i'm going to take a meme detox",
                          ])

bot = commands.Bot(command_prefix=prefix, description="CivBot")

@bot.event
async def on_ready():
    print(getmotd(), "(connected to discord)")
    print("In " + str(len(bot.guilds)) + " guilds")
    for guild in bot.guilds:
        print("    " + guild.name + " - " + str(len(guild.members)) + " members")

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('reddit.com/r/civclassics'))

    with open('resources/VC_temp_storage.pickle', 'wb') as handle:
        pickle1.dump([], handle, protocol=pickle1.HIGHEST_PROTOCOL)

@bot.event
async def on_message(ctx):
    try:
        if ctx.author.id == bot.user.id: return  # ignore self
        else:
            if len(ctx.content) != 0 and prefix == ctx.content[0]:
                await bot.process_commands(ctx)
            else:  # regular chat message
                lower_content = ctx.content.lower()
                if 'delusional' in lower_content:
                    await ctx.channel.send("Edit CivWiki <https://civclassic.miraheze.org/wiki/CivWiki:Editing_Guide>")
                message = ""
                pages = re.findall("\[\[ *([^\]]+) *\]\]", ctx.content)
                for page in pages:
                    message += 'https://civclassic.miraheze.org/wiki/' + page.replace(" ", "_") + "\n"
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

    #really makes you think
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
async def motd(ctx):
    """returns the message of the day"""
    await ctx.channel.send(getmotd())

@bot.command(pass_context=True)
async def animemer(ctx):
    """returns the animemer codex"""
    await ctx.channel.send(file=discord.File('resources/Animemer_template.png'))

@bot.command(pass_context=True)
async def dox(ctx, content):
    """'Doxes' a player"""
    fake = Faker()
    await ctx.channel.send("...Scanning information for " + content + "'s home address...")
    await ctx.channel.trigger_typing()
    await asyncio.sleep(3)
    if random.randrange(0, 6) == 5:
        try:
            await ctx.guild.kick(ctx.message.author, reason="Dox attempt")
            await ctx.channel.send("User was kicked from the server for attempted dox")
        except discord.Forbidden:
            pass
    else:
        Faker.seed(content)
        await ctx.channel.send(":white_check_mark: " + fake.name() + "\n" + fake.address() + "\n")

def draw_derelict(input_string):
    background = Image.open("resources/output.png")
    sign = Image.open("resources/Sign_template.png")
    for i in range(0, len(input_string)):
        font = ImageFont.truetype("resources/Minecraftia.ttf", 42 - (i * 2))
        draw = ImageDraw.Draw(sign)
        start_x = (i * 9) + 18
        end_x = sign.width - ((i * 18) + 28)

        while font.getsize(input_string[i])[0] > end_x - start_x:
            input_string[i] = input_string[i][:-1]

        true_start = (sign.width / 2) - math.floor(font.getsize(input_string[i])[0] / 2) + 7
        draw.text((true_start, (i * 50) + 7), input_string[i], font=font, fill=(0, 0, 0))

    random_scale_factor = random.randrange(1, 5)
    # Resize and maintain aspect ratio
    basewidth = math.floor(max([background.height, background.width]) / (2.2 - random_scale_factor * .1))
    wpercent = (basewidth / float(sign.size[0]))
    hsize = int((float(sign.size[1]) * float(wpercent)))
    sign = sign.resize((basewidth, hsize))

    background.paste(sign, (background.width - sign.width - random.randrange(0, 30),
                            background.height - sign.height + math.floor(
                                sign.height / (10 + random_scale_factor) + random_scale_factor * 10)), sign)
    background.save('resources/output.png', "PNG")

@bot.command(pass_context=True)
async def derelict(ctx, *args):
    """Derelicts an image"""
    result = await find_a_posted_image(ctx)
    if result is not None:
        if str(args) != "()":
            input_string = args[:4]
        else:
            input_string = ['DERELICTION', ctx.message.author.display_name, datetime.datetime.today().strftime('%m/%d/%Y')]

        allowed_chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'abcdefghijklmnopqrstuvwxyz{|}~⌂ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜø£Ø×ƒáíóúñÑªº¿®¬½¼¡«»"
        for v in range(0, len(input_string)):
            for char in list(input_string[v]):
                if char not in allowed_chars:
                    input_string[v] = input_string[v].replace(char, '')

        params = functools.partial(draw_derelict, input_string)
        run_draw = await bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))

def draw_verb_at_image(filepath):
    inner = Image.open("resources/output.png")
    outer = Image.open(filepath)
    input_im = inner.resize((415, 415))
    newImage = Image.new('RGB', (outer.width, outer.height))
    newImage.paste(input_im, (54, 37))
    newImage.paste(outer, (0, 0), outer)
    newImage.save('resources/output.png', "PNG")

async def verb_at_image(ctx, location):
    result = await find_a_posted_image(ctx)
    if result is not None:
        params = functools.partial(draw_verb_at_image, location)
        run_draw = await bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))

@bot.command(pass_context=True)
async def cryat(ctx, *args):
    """Crys at the image"""
    await verb_at_image(ctx, "resources/Cry_template.png")

@bot.command(pass_context=True)
async def laughat(ctx, *args):
    """Laughs at the image"""
    await verb_at_image(ctx, "resources/Laugh_template.png")

@bot.command(pass_context=True)
async def pearl(ctx, *, content):
    """Pearls a player."""
    if len(content.split(" ")) > 1:
        players = []
        for p in content.split(" ")[:2]:
            # https://github.com/clerie/mcuuid/issues/1
            if GetPlayerData(p) and hasattr(GetPlayerData(p), 'username'):
                players.append(GetPlayerData(p).username)
            elif not re.match('^(\w|d){3,16}', p):
                await ctx.channel.send("Invalid usernames supplied")
                return
            else:
                players.append(re.match('^(\w|d){3,30}', p).group(0))

        date = datetime.datetime.today().strftime('%m/%d/%Y')
        if len(content.split(" ")) > 2 and re.match("\d{1,2}\/\d{1,2}\/\d{1,4}",content.split(" ")[2]):
            date = re.match("\d{1,2}\/\d{1,2}\/\d{1,4}",content.split(" ")[2]).group(0)

        params = functools.partial(generate_pearl_image, players[0], players[1], date)
        run_draw = await bot.loop.run_in_executor(None, params)
        bot_message = await ctx.channel.send(file=discord.File("resources/output.png"))

        with open('resources/pearl locations.txt', 'r') as file:
            locations = json.load(file)
        await asyncio.sleep(1)
        locations[players[0].lower()] = bot_message.jump_url
        with open('resources/pearl locations.txt', 'w') as file:
            json.dump(locations, file)

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






def draw_dont_care(username):
    r = requests.get("https://mc-heads.net/avatar/" + str(username) + "/325.png")

    with open("resources/test.png", 'wb') as f:
        f.write(r.content)

    temp = Image.open("resources/test.png")
    # temp = ImageOps.invert(temp)

    half_area = (0, 0, temp.height / 2, temp.width)
    new = temp.crop(half_area)

    new_image = Image.new('RGB', (temp.height, temp.width))
    new_image.paste(new)
    flip = ImageOps.mirror(new)
    new_image.paste(flip, (int(temp.width / 2), 0))

    upper = Image.open("resources/Uppergulf.png")
    new_image = new_image.convert('RGBA')
    new_image.paste(upper, (0, 0), upper.convert('RGBA'))
    new_image.save('resources/output.png', "PNG")


@bot.command(pass_context=True)
async def dont_care(ctx, content):
    if not GetPlayerData(content).valid:
        await ctx.channel.send(
            discord.utils.escape_markdown(discord.utils.escape_mentions(
                content)) + " does not appear to be a valid player. Are you sure you typed correctly?")
    else:
        params = functools.partial(draw_dont_care, content)
        run_draw = await bot.loop.run_in_executor(None, params)
        bot_message = await ctx.channel.send(file=discord.File("resources/output.png"))

def draw_weezer(players):
    to_send = []

    drawn_players = ["", "", "", ""]
    joiners = ""
    rect_corners = [
        [(3, 300), (78, 94)],
        [(78, 300), (148, 107)],
        [(153, 300), (222, 94)],
        [(226, 300), (294, 100)]
    ]
    background = Image.open("resources/weezer template.png")
    draw = ImageDraw.Draw(background)

    players = players[:4]
    for p in players:
        if not GetPlayerData(p).valid:
            to_send.append(discord.utils.escape_markdown(discord.utils.escape_mentions(p)) + " does not appear to be a valid player. Are you sure you typed correctly?")
        else:
            selected = False
            while not selected:
                r = random.randint(-1, 3)
                if drawn_players[r] == "":
                    drawn_players[r] = GetPlayerData(p).username
                    draw.rectangle((rect_corners[r][0], rect_corners[r][1]), fill="#00acea")
                    selected = True

    out_2 = None
    if len(players) > len(to_send):
        for x in range(0, len(drawn_players)):
            if drawn_players[x] != "":
                r = requests.get("https://mc-heads.net/player/" + GetPlayerData(drawn_players[x]).uuid + "/" + str(
                    (rect_corners[x][0][1] - rect_corners[x][1][1]) / 2) + ".png")
                with open("resources/test.png", 'wb') as f:
                    f.write(r.content)
                playertopaste = Image.open("resources/test.png")
                background.paste(playertopaste, (rect_corners[x][0][0], rect_corners[x][1][1]),
                                 mask=playertopaste)
                joiners += ", " + drawn_players[x]
        background.save('resources/output.png', "PNG")
        if sum([x != "" for x in drawn_players]) > 1:
            k = joiners.rfind(", ")
            joiners = joiners[:k] + " and" + joiners[k + 1:]

        out_2 = "**Oh my God" + joiners + " joined weezer!**"
    return to_send, out_2



@bot.command(pass_context=True)
async def joinedweezer(ctx, *args):
    """`!joinedweezer <player1> <player2> <player3> <player4>`\nListing one player (minecraft username) is required, other three are optional.\nNow you too can join Weezer!"""
    params = functools.partial(draw_weezer, list(args))
    msgs, image = await bot.loop.run_in_executor(None, params)
    for x in msgs:
        await ctx.channel.send(x)
    if image is not None:
        await ctx.channel.send(image, file=discord.File('resources/output.png'))

def draw_getalong(players):
    img_shirt = Image.open("resources/shirt.png")
    background = Image.new('RGB', (600, 500), color=(255, 255, 255))

    for i, player in enumerate(players):
        r = requests.get("https://mc-heads.net/player/" + player + "/160.png")
        background.paste(Image.open(io.BytesIO(r.content)), ((150 + i * 150), (110 - i * 12)))
    background.paste(img_shirt, (0, 0), mask=img_shirt)
    background.save('resources/output.png', "PNG")

@bot.command(pass_context=True)
async def getalong(ctx, player1, player2):
    """First we botted farms, then we botted vaults, now we finally have an opportunity to bot world peace."""
    players = [player1, player2]
    for x in players:
        if not GetPlayerData(x).valid:
            await ctx.channel.send(
                discord.utils.escape_markdown(discord.utils.escape_mentions(
                    x)) + " does not appear to be a valid player. Are you sure you typed correctly?")
            return
    params = functools.partial(draw_getalong, players)
    msg = await bot.loop.run_in_executor(None, params)
    await ctx.channel.send(file=discord.File('resources/output.png'))


@bot.command(pass_context=True)
async def whereis(ctx, x, z):
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
        for d in range(0, 14):
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
        await ctx.channel.send((str(out) + "```"))


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

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    token = config.get('auth', 'token')

    initial_extensions = ['cogs.VoiceRelay']
    for extension in initial_extensions:
        bot.load_extension(extension)

    while True:
        try:
            bot.run(token)
        except Exception as e:
            print("Error", e)
        print("Waiting until restart")
        time.sleep(10)
