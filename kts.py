from discord.ext import commands
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, defer
from quarry.net.auth import Profile
from quarry.net.client import ClientFactory, SpawningClientProtocol
import time, logging, datetime, asyncio, discord, random, queue, threading, json
import aiohttp, async_timeout
from bs4 import BeautifulSoup
import re
from PIL import Image, ImageDraw, ImageFont
import string
import requests
from faker import Faker
import math
from _operator import itemgetter

from config import *

prefix = "&"

buffer = 10
mc_q = queue.Queue(buffer)
ds_q = queue.Queue(buffer)

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

    req_width = 129 + font.getsize(pearled_player + "#" + code)[0] + 23
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


async def find_a_posted_image(ctx):
    if len(ctx.message.attachments) == 0:
        check_above = await ctx.message.channel.history(limit=12).flatten()
        for o in check_above:
            if len(o.attachments) != 0:
                return requests.get(o.attachments[0].url)
    else:
        return requests.get(ctx.message.attachments[0].url)
    return

####################
# quarry bot setup #
####################

playerLogInterval = 10

print_player_login_logout = False

def timestring():
    mtime = datetime.datetime.now()
    return "[{:%H:%M:%S}] ".format(mtime)

def datestring():
    mtime = datetime.datetime.now()
    return "[{:%d/%m/%y}] ".format(mtime)

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

def get_rand_message():
    with open ("welcomemessages.txt", "r") as welcomes:
        return random.choice(welcomes.readlines()).strip("\n")

class OliveClientProtocol(SpawningClientProtocol):
    def setup(self):
        self.players = {}
        self.playerActions = {}
        self.newplayers = []
        self.welcomeLog = {}
        print ("oliveclientprotocol setup debug message")
        self.ticker.add_loop(40, self.process_mc_q)
        self.lastLogTime = time.time()

    #serverbound packets
    def send_chat(self, text):
        self.send_packet("chat_message", self.buff_type.pack_string(text))
    
    #clientbound packets
    def packet_chat_message(self, buff):
        p_text = buff.unpack_chat()
        p_position = buff.unpack("B")
        print (timestring() + str (p_text))
        l_text = str(p_text).split()
        if " ".join(l_text[1:]) == "is brand new!":
            welcome_msg = get_rand_message()
            ds_q.put({"key":"new player", "name":l_text[0], "msg":welcome_msg})
            self.newplayers.append(l_text[0])
            self.ticker.add_delay(1800, lambda: self.send_welcome_message1(welcome_msg))
            #self.ticker.add_delay(1900, self.send_welcome_message2)
        elif l_text[0] == "From":
            name = l_text[1].strip(":")
            try:
                welcome = self.welcomeLog[name]
            except:
                welcome = "(no recorded welcome message for this player)"
            ds_q.put({"key":"relaymessage", "name":name, "content":" ".join(l_text[2:]), "welcome":welcome})

    def packet_player_list_item(self, buff):
        logTime = int (time.time())
        login_time = str (int (time.time()))
        p_action = buff.unpack_varint()
        p_count = buff.unpack_varint()
        for i in range (p_count):
            p_uuid = buff.unpack_uuid()
            if p_action == 0:  # ADD_PLAYER
                p_player_name = buff.unpack_string()
                p_properties_count = buff.unpack_varint()
                p_properties = {}
                for j in range(p_properties_count):
                    p_property_name = buff.unpack_string()
                    p_property_value = buff.unpack_string()
                    p_property_is_signed = buff.unpack('?')
                    if p_property_is_signed:
                        p_property_signature = buff.unpack_string()
                    p_properties[p_property_name] = p_property_value
                p_gamemode = buff.unpack_varint()
                p_ping = buff.unpack_varint()
                p_has_display_name = buff.unpack('?')
                if p_has_display_name:
                    p_display_name = buff.unpack_chat()
                else:
                    p_display_name = None
                self.players[p_uuid] = {"name": p_player_name,
                                        "properties": p_properties,
                                        "gamemode": p_gamemode,
                                        "ping": p_ping,
                                        "display_name": p_display_name,
                                        "login_time": login_time}
                if print_player_login_logout:
                    print (timestring() + str(p_player_name) + " joined the game")
                self.playerActions[self.players[p_uuid]["name"]] = "logged in"
            elif p_action == 1:  # UPDATE_GAMEMODE
                p_gamemode = buff.unpack_varint()
                if p_uuid in self.players:
                    self.players[p_uuid]['gamemode'] = p_gamemode
            elif p_action == 2:  # UPDATE_LATENCY
                p_ping = buff.unpack_varint()
                if p_uuid in self.players:
                    self.players[p_uuid]['ping'] = p_ping
            elif p_action == 3:  # UPDATE_DISPLAY_NAME
                p_has_display_name = buff.unpack('?')
                if p_has_display_name:
                    p_display_name = buff.unpack_chat()
                else:
                    p_display_name = None
                if p_uuid in self.players:
                    self.players[p_uuid]['display_name'] = p_display_name
            elif p_action == 4:  # REMOVE_PLAYER
                if p_uuid in self.players:
                    if print_player_login_logout:
                        print (timestring() + self.players[p_uuid]["name"] + " left the game")
                    self.playerActions[self.players[p_uuid]["name"]] = "logged out"
                    del self.players[p_uuid]
        if logTime > self.lastLogTime + playerLogInterval:
            ds_q.put({"key":"loginlogout", "actions":self.playerActions})
            self.lastLogTime = logTime
            self.playerActions = {}

    def packet_disconnect(self, buff):
        p_text = buff.unpack_chat()
        print (timestring() + str (p_text))

    #callbacks
    def player_joined(self):
        print (timestring() + "joined the game as " + self.factory.profile.display_name + ".")

    def send_welcome_message1(self, message):
        name = self.newplayers.pop(0)
        self.welcomeLog[name] = message
        self.send_chat("/tell "+name+" "+message)
        with open ("welcomelog.txt", "a+") as log:
            log.write(name + " : " + message)

    #methods
    def process_mc_q(self):
        if not mc_q.empty():
            package = mc_q.get()
            #print (package)
            if package["key"] == "debug":
                ds_q.put({"key":"relay", "channel":package["channel"], "content":"debug relay"})
            elif package["key"] == "messagerelay":
                self.send_chat("/tell " + package["name"] + " " + package["content"])
                ds_q.put({"key":"relay", "channel":package["channel"], "content":"welcome messages for " + package["name"] + " queued"})
            elif package["key"] == "shutdown":
                reactor.stop()
            else:
                print (package)
            
class OliveClientFactory(ReconnectingClientFactory, ClientFactory):
    protocol = OliveClientProtocol
    def startedConnecting(self, connector):
        self.maxDelay = 60
        print (timestring() + "connecting to " + connector.getDestination().host + "...")
        #print (self.__getstate__())
    def clientConnectionFailed(self, connector, reason):
        print ("connection failed: " + str (reason))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    def clientConnectionLost(self, connector, reason):
        print(timestring() + "disconnected:" + str(reason).split(":")[-1][:-2])
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

#####################
# discord bot setup #
#####################

def getmotd():
    return random.choice(["olive",
                          "olives",
                          "kalamata olive",
                          "kalamata olives",
                          "sliced kalamata olives",
                          "sliced kalamata olives in brine",
                          "pre-owned sliced kalamata olives in brine",
                          "i think i'm going to take a meme detox",
                          ])

guild = 613024898024996914
relayCategory = 665296878254161950

kdb = commands.Bot(command_prefix=prefix, description=getmotd())

brandNewMsgChannel = 664474265277693982

def search_relay_channel(name):
    #print ("searching for", name)
    for channel in kdb.get_all_channels():
        if channel.category == kdb.get_channel(relayCategory):
            if str (channel.name).lower() == name.lower():
                #print (channel)
                return channel
    return None

def log_new_player(name):
    with open ("newplayerlog.txt", mode="a+") as log:
        log.write(str(datestring()+timestring()+name+"\n"))


def log_message_response(name):
    try:
        with open ("messageresponselog.txt", mode="r+") as log:
            for line in log.readlines():
                if name in line:
                    return
    except FileNotFoundError:
        with open ("messageresponselog.txt", mode="a+") as log:
            log.write(str(datestring()+timestring()+name+"\n"))


async def process_ds_q():
    await kdb.wait_until_ready()
    while not kdb.is_closed():
        #print ("discord loop alive")
        if not ds_q.empty():
            package = ds_q.get()
            #print (package)
            try:
                if package["key"] == "new player":
                    s = "" + package["name"] + " is brand new!\n"+package["msg"]
                    c = kdb.get_channel(brandNewMsgChannel)
                    await c.send(clean_text_for_discord(s))
                    #await kdb.get_guild(guild).create_text_channel(package["name"], category=kdb.get_channel(relayCategory))
                    log_new_player(package["name"])
                elif package["key"] == "relay":
                    await package["channel"].send(clean_text_for_discord(package["content"]))
                elif package["key"] == "relaymessage":
                    channel = search_relay_channel(package["name"])
                    if channel:
                        await channel.send("**" + clean_text_for_discord(package["name"]) + "**: " + clean_text_for_discord(package["content"]))
                    else:
                        log_message_response(package["name"])
                        await kdb.get_guild(guild).create_text_channel(package["name"], category=kdb.get_channel(relayCategory))
                        channel = search_relay_channel(package["name"])
                        await channel.send(clean_text_for_discord(package["welcome"]))
                        await channel.send("**" + clean_text_for_discord(package["name"]) + "**: " + clean_text_for_discord(package["content"]))
                elif package["key"] == "loginlogout":
                    for player in package["actions"].keys():
                        channel = search_relay_channel(player)
                        if channel:
                            await channel.send(clean_text_for_discord(player+" "+package["actions"][player]))
                else:
                    print ("unknown package")
                    print (package)
            except KeyError:
                print ("package error")
                print (package)
        await asyncio.sleep(2)
    print ("discord dead how will you recover retard")

@kdb.event
async def on_ready():
    print (getmotd(), "(connected to discord)")
    await kdb.loop.create_task(process_ds_q())
    print ("discord debug on ready")

@kdb.event
async def on_message(ctx):
    try:
        if ctx.author.id == kdb.user.id: return  # ignore self
        if ctx.channel.category.id == relayCategory:
            try:
                if prefix == ctx.content[0]:
                    await kdb.process_commands(ctx)
                else:
                    mc_q.put({"key":"messagerelay", "name":str(ctx.channel.name), "content":ctx.content})
            except:
                pass
        else:
            if len(ctx.content) != 0 and prefix == ctx.content[0]:
                await kdb.process_commands(ctx)
            else:  # regular chat message
                lower_content = ctx.content.lower()
                if 'delusional' in lower_content:
                    await ctx.channel.send("Edit CivWiki <https://civclassic.miraheze.org/wiki/CivWiki:Editing_Guide>")
                if ctx.content.startswith('[[') and ctx.content.endswith(']]'):
                    await ctx.channel.send('https://civclassic.miraheze.org/wiki/' + ctx.content[2:-2].replace(" ","%s"))

    except AttributeError:
        print ("From " + str (ctx.author) + ": " + ctx.content)


#uncategorised
@kdb.command(pass_context=True)
async def respond(ctx):
    """test command"""
    await ctx.message.delete()
    await ctx.channel.send(get_response())

@kdb.command(pass_context=True)
async def motd(ctx):
    """returns the message of the day"""
    await ctx.channel.send(getmotd())

@kdb.command(pass_context=True)
async def animemer(ctx):
    """returns the animemer codex"""
    await ctx.channel.send(file=discord.File('resources/Animemer_template.png'))

@kdb.command(pass_context=True)
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


@kdb.command(pass_context=True)
async def derelict(ctx, *args):
    """Derelicts an image"""
    result = await find_a_posted_image(ctx)
    if result is not None:
        with open("resources/output.png", 'wb') as f:
            f.write(result.content)

        background = Image.open("resources/output.png")
        sign = Image.open("resources/Sign template.png")

        if str(args) != "()":
            input_string = args[:4]
        else:
            input_string = ['DERELICTION', ctx.message.author.display_name, datetime.datetime.today().strftime('%m/%d/%Y')]

        allowed_chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'abcdefghijklmnopqrstuvwxyz{|}~⌂ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜø£Ø×ƒáíóúñÑªº¿®¬½¼¡«»"
        for v in range(0, len(input_string)):
            for char in list(input_string[v]):
                if char not in allowed_chars:
                    input_string[v] = input_string[v].replace(char, '')

        for i in range(0, len(input_string)):
            font = ImageFont.truetype("resources/Minecraftia.ttf", 42 - (i * 2))
            draw = ImageDraw.Draw(sign)
            start_x = (i * 9) + 18
            end_x = sign.width - ((i * 18) + 28)

            while font.getsize(input_string[i])[0] > end_x - start_x:
                input_string[i] = input_string[i][:-1]

            true_start = (sign.width/2) - math.floor(font.getsize(input_string[i])[0] / 2) + 7
            draw.text((true_start, (i * 50) + 7), input_string[i], font=font, fill=(0, 0, 0))

        random_scale_factor = random.randrange(1, 5)

        #Resize and maintain aspect ratio
        basewidth = math.floor(max([background.height, background.width]) / (2.2 - random_scale_factor * .1))
        wpercent = (basewidth / float(sign.size[0]))
        hsize = int((float(sign.size[1]) * float(wpercent)))
        sign = sign.resize((basewidth, hsize))

        background.paste(sign, (background.width - sign.width - random.randrange(0, 30),
                                background.height - sign.height + math.floor(
                                    sign.height / (10 + random_scale_factor) + random_scale_factor * 10)), sign)

        background.save('resources/output.png', "PNG")
        await ctx.channel.send(file=discord.File('resources/output.png'))




async def verb_at_image(ctx, location):
    result = await find_a_posted_image(ctx)
    if result is not None:
        with open("resources/output.png", 'wb') as f:
            f.write(result.content)
        inner = Image.open("resources/output.png")
        outer = Image.open(location)
        input_im = inner.resize((415, 415))
        newImage = Image.new('RGB', (outer.width, outer.height))
        newImage.paste(input_im, (54, 37))
        newImage.paste(outer, (0, 0), outer)
        newImage.save('resources/output.png', "PNG")
        await ctx.channel.send(file=discord.File('resources/output.png'))


@kdb.command(pass_context=True)
async def cryat(ctx, *args):
    """Crys at the image"""
    await verb_at_image(ctx, "resources/Cry_template.png")


@kdb.command(pass_context=True)
async def laughat(ctx, *args):
    """Laughs at the image"""
    await verb_at_image(ctx, "resources/Laugh_template.png")


@kdb.command(pass_context=True)
async def pearl(ctx, *, content):
    """Pearls a player."""
    if len(content.split(" ")) > 1:
        players = []
        for p in content.split(" ")[:2]:
            # https://github.com/clerie/mcuuid/issues/1
            # if GetPlayerData(p) and hasattr(GetPlayerData(p), 'username'):
            #     players.append(GetPlayerData(p).username)
            if not re.match('^(\w|d){3,16}', p):
                await ctx.channel.send("Invalid usernames supplied")
                return
            else:
                players.append(p)

        date = datetime.datetime.today().strftime('%m/%d/%Y')
        if len(content.split(" ")) > 2 and re.match("\d{1,2}\/\d{1,2}\/\d{1,4}",content.split(" ")[2]):
            date = re.match("\d{1,2}\/\d{1,2}\/\d{1,4}",content.split(" ")[2]).group(0)

        generate_pearl_image(players[0], players[1], date)
        bot_message = await ctx.channel.send(file=discord.File("resources/output.png"))

        with open('resources/pearl locations.txt', 'r') as file:
            locations = json.load(file)
        await asyncio.sleep(1)
        locations[players[0].lower()] = bot_message.jump_url
        with open('resources/pearl locations.txt', 'w') as file:
            json.dump(locations, file)

@kdb.command(pass_context=True)
async def pplocate(ctx, *, content):
    """Locates a players pearl"""
    with open('resources/pearl locations.txt', 'r') as file:
        locations = json.load(file)
    if content.lower() in locations:
        await ctx.channel.send(locations[content])
    else:
        await ctx.channel.send("**" + clean_text_for_discord(content) + "**'s pearl could not be located")

@kdb.command(pass_context=True)
async def ppfree(ctx, *, content):
    """Frees a players pearl"""
    with open('resources/pearl locations.txt', 'r') as file:
        locations = json.load(file)
    if content.lower() in locations:
        await ctx.channel.send("You freed **" + clean_text_for_discord(content) + "**")
        del locations[content.lower()]
        with open('resources/pearl locations.txt', 'w') as file:
            json.dump(locations, file)

@kdb.command(pass_context=True)
async def wiard(ctx, *, content):
    """wiardifies a message"""
    await ctx.channel.send(wiardify(content))

@kdb.command(pass_context=True)
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
                if ccmap['features'][ind]["Zoom Visibility"] == 1:
                    xtra = " ::"

            out += str(distances[list(distances)[d]]).rjust(4, " ") + "  blocks " + (dirs[ix % len(dirs)]).rjust(5,
                                                                                                                 " ") + "  " + \
                   ccmap['features'][ind]['name'] + xtra + "\n"
        await ctx.channel.send((str(out) + "```"))

@kdb.command(pass_context=True)
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
    # # TODO check ['status'] == 'ok'
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

#discord welcome messages
@kdb.command(pass_context=True)
async def welcomeadd(ctx, *, content):
    """adds a welcome message to the list"""
    with open ("welcomes.txt", "a+") as welcomes:
        welcomes.write(content + "\n")
    await ctx.channel.send("added welcome message")

@kdb.command(pass_context=True)
async def welcomeget(ctx):
    """returns current welcome messages"""
    i = ""
    with open ("welcomes.txt", "r") as welcomes:
        j = 1
        for welcome in welcomes.readlines():
            if len (i + str (j) + ". " + welcome) > 1999:
                await ctx.channel.send(i)
                i = ""
            i += (str (j) + ". " + welcome)
            j += 1
    await ctx.channel.send(i)

@kdb.command(pass_context=True)
async def playerlog(ctx, *, content):
    """returns the welcome message sent to a given player"""
    with open ("welcomelog.txt", "r") as log:
        for line in log.readlines():
            if line.split(" : ")[0].lower() == content.lower():
                await ctx.channel.send(line.split(" : ")[1])

@kdb.command(pass_context=True)
async def welcomeremove(ctx, *, content):
    """removes a given welcome messages"""
    w = []
    try:
        i = int(content)
    except:
        await ctx.channel.send("cannot convert to int (probably)")
        return
    with open ("welcomes.txt", "r") as welcomes:
        w = welcomes.readlines()
        try:
            del w[i-1]
        except:
            await ctx.channel.send("list index out of range (probably)")
            return
    with open ("welcomes.txt", "w") as welcomes:
        for line in w:
            welcomes.write(line)
    await ctx.channel.send("successfully removed message (probably)")

#relay channel management
@kdb.command(pass_context=True)
async def relayspawn(ctx, *, content):
    """creates a relay channel with a specified name"""
    await kdb.get_guild(guild).create_text_channel(content, category=kdb.get_channel(relayCategory))

@kdb.command(pass_context=True)
async def relaykill(ctx, *, content="this"):
    """deletes a relay channel with the specified name"""
    if content == "this":
        channel = ctx.channel
        if channel.category.id == relayCategory:
            pass
        else:
            return
    else:
        channel = search_relay_channel(content)
    try:
        await channel.delete()
    except:
        pass

#debug commands
@kdb.group(pass_context=True)
async def debug(ctx):
    """debug commands"""

@debug.command(pass_context=True)
async def shutdown(ctx):
    """shuts the bot down"""
    mc_q.put({"key":"shutdown"})
    await kdb.close()

@debug.command(pass_context=True)
async def mc(ctx):
    """checks if minecraft is connected (sometimes)"""
    mc_q.put({"key":"debug", "channel":ctx.channel})

#######
# run #
#######

@defer.inlineCallbacks
def mc_main():
    profile = yield Profile.from_credentials(username, password)
    factory = OliveClientFactory(profile)
    try:
        factory = yield factory.connect(host, port)
    except Exception as e:
        print (e)

def mc_error(err):
    raise err

if __name__ == "__main__":
    mc_main()
    mcThread = threading.Thread(target=reactor.run, kwargs={"installSignalHandlers":0})
    mcThread.start()
    kdb.run(token)
