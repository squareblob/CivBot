from discord.ext import commands
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, defer
from quarry.net.auth import Profile
from quarry.net.client import ClientFactory, SpawningClientProtocol
import time, logging, datetime, asyncio, discord, random, queue, threading

from config import *

buffer = 10
mc_q = queue.Queue(buffer)
ds_q = queue.Queue(buffer)

def clean_text_for_discord(text):
    text = text.replace("_", "\_")
    text = text.replace("*", "\*")
    text = text.replace("~~", "\~~")
    return text

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
    with open ("welcomes.txt", "r") as welcomes:
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

kdb = commands.Bot(command_prefix="%", description=getmotd())

botInfoChannel = 664293935362998346

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
                    c = kdb.get_channel(botInfoChannel)
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
                if "%" == ctx.content[0]:
                    await kdb.process_commands(ctx)
                else:
                    mc_q.put({"key":"messagerelay", "name":str(ctx.channel.name), "content":ctx.content})
            except:
                pass
        else:
            if "%" == ctx.content[0]:
                await kdb.process_commands(ctx)
            else:  # regular chat message
                lower_content = ctx.content.lower()
                if 'delusional' in lower_content:
                    await ctx.channel.send("Edit CivWiki <https://civclassic.miraheze.org/wiki/CivWiki:Editing_Guide>")
                if ctx.content.startswith('[[') and ctx.content.endswith(']]'):
                    await ctx.channel.send('https://civclassic.miraheze.org/wiki/' + ctx.content[2:-2])

    except AttributeError:
        print ("From " + str (ctx.author) + ": " + ctx.content)


#uncategorised
@kdb.command(pass_context=True)
async def hello(ctx):
    """test command"""
    await ctx.channel.send("COMMAND INVOKED")

@kdb.command(pass_context=True)
async def motd(ctx):
    """returns the motd"""
    await ctx.channel.send(getmotd())

@kdb.command(pass_context=True)
async def wiard(ctx, *, content):
    """wiardifies a message"""
    await ctx.channel.send(wiardify(content))

#discord welcome messages
@kdb.group(pass_context=True)
async def welcome(ctx):
    """minecraft welcome message management"""

@welcome.command(pass_context=True)
async def add(ctx, *, content):
    """adds a welcome message to the list"""
    with open ("welcomes.txt", "a+") as welcomes:
        welcomes.write(content + "\n")
    await ctx.channel.send("added welcome message")

@welcome.command(pass_context=True)
async def get(ctx):
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

@welcome.command(pass_context=True)
async def playerlog(ctx, *, content):
    """returns the welcome message sent to a given player"""
    with open ("welcomelog.txt", "r") as log:
        for line in log.readlines():
            if line.split(" : ")[0].lower() == content.lower():
                await ctx.channel.send(line.split(" : ")[1])

@welcome.command(pass_context=True)
async def remove(ctx, *, content):
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
@kdb.group(pass_context=True)
async def relay(ctx, *, content):
    """relay channel management"""
        
@relay.command(pass_context=True)
async def spawn(ctx, *, content):
    """creates a relay channel with a specified name"""
    await kdb.get_guild(guild).create_text_channel(content, category=kdb.get_channel(relayCategory))

@relay.command(pass_context=True)
async def kill(ctx, *, content="this"):
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
