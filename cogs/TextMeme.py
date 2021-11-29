import asyncio
import random
import json
import discord
import pycountry
from discord.ext import commands
from discord.utils import escape_mentions

from perchance import perchance_gen, perchance_parse

perchance_civ_classic = perchance_parse(open('resources/TextMeme/perchance.txt').read())

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


class TextMeme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.command(pass_context=True)
    async def oracle(self, ctx):
        """Gives a oraclist response"""
        wordlist = ["That is definitely not canon and may in fact be illegal",
                    "Roleplay Detected",
                    "this is the sort of thing said by the sort of people squareblob sort of vowed to sort of destroy",
                    "Good luck you little bingus",
                    "you can't create an idea, idiot",
                    "Supercringe giganormie"]
        await ctx.channel.send(random.choice(wordlist))

    @commands.command(pass_context=True)
    async def thraldrek(self, ctx):
        """Gives a thraldrek response"""
        country_name = random.choice(list(pycountry.countries)).name
        if random.randint(0, 200) == 1:
            country_name = "Thrain Family Forest"
        wordlist = ["Isn't " + ctx.author.name + " from " + country_name]
        await ctx.channel.send(random.choice(wordlist))

    @commands.command(pass_context=True)
    async def topher(self, ctx):
        """Gives a topher response"""
        # todo get most recent 10 messages, and do not reuse.
        lines = open('resources/TextMeme/wordlist_topher.txt').read().splitlines()
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
        await ctx.channel.send(escape_mentions(message))
        if random.randint(0, 3) == 3:
            await ctx.channel.send(file=discord.File('resources/TextMeme/topher.gif'))

    @commands.command(pass_context=True)
    async def freestyle(self, ctx):
        """Gives a freestyle response"""
        await ctx.channel.send(file=discord.File('resources/TextMeme/topher.gif'))

    @commands.command(pass_context=True)
    async def respond(self, ctx):
        """Gives a Civ response"""
        await ctx.channel.send(get_response())

    @commands.command(pass_context=True)
    async def generateplugin(self, ctx, content='1'):
        """Generates a civ server plugin"""
        with open('resources/TextMeme/Techs.txt') as f:
            plugin_base = [line.rstrip().replace(" ", "_") for line in f]
        prefix = ["Better", "Civ", "Realistic", "Old", "Simple", "Meme", "Add", "Quirky"]
        base = ["Biomes", "Bastion", "Item", "Citadel", "Enchanting", "Combat", "Brewery", "Border", "Teleports",
                "Instant_Death", "Block_Puzzles", "Information_Overload", "Disinformation", "Gravity", "Bullet_Hell",
                "Brawl", "Disease", "Crop"]
        plugin_base = plugin_base + base
        suffix = ["Core", "Alert", "-spawn", "Colors", "Layer", "Exchange", "Mod", "Stick", "Mana", "Spy", "Plus",
                  "Manager", "Fix", "Alts", "Tweaks", "Tools", "fuscator", "Pearl", "limits", "Ore", "egg", "Shards",
                  "Cull", "Contraptions", "PvP", "Bank"]

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

    @commands.command(pass_context=True)
    async def wiard(self, ctx, *, content):
        """wiardifies a message"""
        await ctx.channel.send(wiardify(escape_mentions(content)))

    @commands.command(pass_context=True)
    async def unwiard(self, ctx, *, content):
        """unwiardifies a message"""
        await ctx.channel.send(unwiardify(escape_mentions(content)))

    @commands.command(pass_context=True)
    async def drama(self, ctx):
        """Generates CivClassic drama"""
        await ctx.channel.send(escape_mentions(perchance_gen(perchance_civ_classic)))

    @commands.command(pass_context=True)
    async def pickle(self, ctx, content):
        """Pickles a player with a food related adjective"""
        with open('resources/TextMeme/Food adjectives.txt') as f:
            lines = f.read().splitlines()
        adjs = []
        for a in lines:
            if a[0].casefold() == content[0].casefold():
                adjs.append(a)
        if content.casefold() == "pirater":
            adjs = ["pickled"]
        if len(adjs) > 0:
            await ctx.channel.send(random.choice(adjs).capitalize() + " " + escape_mentions(content))

    @commands.command(pass_context=True)
    async def trolling(self, ctx):
        """Things we do a little of"""
        troll_words = "bohling, boling, bolling, boweling, bowelling, bowling, coaling, doling, drolling, foaling, growling, holing, koelling, loling, moling, owling, poling, polling, prolling, rohling, roling, rowling, scrolling, shoaling, soling, strolling, tholing, toling, tolling, trolling, wauling, yowling, bankrolling, cajoling, carolling, condoling, consoling, controlling, enrolling, erholung, extolling, inscrolling, lawn bowling, paroling, patrolling, unrolling"
        selection = random.choice(troll_words.split(", "))
        phrase = "We do a little " + selection
        emoji = discord.utils.get(self.bot.emojis, name='trolle')
        if emoji:
            phrase += " " + str(emoji)
        await ctx.channel.send(phrase)

    @commands.command(pass_context=True)
    async def pac(self, ctx):
        """PacGaming"""
        wordlist = ["Gaming", "Blaming", "Claiming", "Taming", "Statue", "Framing", "Naming", "Aiming"]
        message = "Pac" + random.choice(wordlist)
        await ctx.channel.send(message)
        
    @commands.command(pass_context=True)
    async def guy(self, ctx):
        """Quirky little Civbot guy"""
        adjectives = ["quirky", "wacky", "weird", "hsm", "wholesome", "squishy", "squeezable", "funny", "stupid", "naughty", "adorable", "pleasant", "big", "speedy", "clever", "profound", "violent", "peaceful", "spunky", "that", "comfy"]
        names = ["blob", "squareblob", "topher", "godo", "nebula", "ahme", "gjum", "oange", "thraldrek", "allen", "oracle", "pac", "metrix", "specific", "civbot", "kapre", "oracle", "imp", "minemaster", "llamma", "sambonusg"]
        message =  random.choice(adjectives) + " little " + random.choice(names) + " guy"
        await ctx.channel.send(message)
       
    @commands.command(pass_context=True)
    async def allen(self, ctx):
        """Dispenses some allenist thought"""
        wordlist = ["we eat of squareblob's flesh and drink of squareblob's blood", 
                    "you are all in squarecords none of you are free of sin", 
                   "square never does anything he feels pressured to; natural elasticity allows him to retain shape after squeezing",
                   "if you see me afking irl just kill me",
                   "kill",
                   "mts academy of linguistics is a prescriptivist pseudoscientific diploma mill",
                   "i have always enjoyed the aesthetics of a dictatorship where you go to jail if you mess up the 7 stream recycling",
                    "oh",
                   "i live in considerable fear that i will go down in history like dr oracle, known for like three mildly funny quotes total because of my inclusion in a bot",
                   "my piss memes have literally changed the course of mta history nobody needs to be told",
                   "WHERE IS SQUAREBLOB I WANT SQUAREBLOB",
                   ":blueone: is like having done something transgressive, but you arent sorry for it, and in fact may be indicating that in your lack of remorse you will do something more transgressive though it's not being brazen or flamey about it: it's a sort of"
                   ]
        await ctx.channel.send(random.choice(wordlist))
                 
    @commands.command(pass_context=True)
    async def askthemayor(self, ctx):
        """Answers a question from the populace"""
        wordlist = ["Yes.",
                    "Yes, IMO.",
                    "Yeah.",
                    "Aye.",
                    "Naye.",
                    "No.",
                    "No, IMO.",
                    ":smil:",
                    ":blueone:",
                    ":skull:",
                    ":really:",
                    "hsm",
                    "Wholesale.",
                    "Terrifying.",
                    "Blocked.",
                    "Anyone wanna kiss (in Minecraft)",
                    "I disagree.",
                    "I generally agree.",
                    "cool.jpg",
                    "Many such cases.",
                    "That would be optimal.",
                    "I'm still not sure what you mean.",
                    "Can you elaborate on this?",
                    "Not funny, didn't ask, plus I'm a bot.",
                    "Oh.",
                    "Sorry.",
                    "This user has a registered bald head. Learn more about Discord's new safety policy at https://discord.com/guidelines",
                    "Ok rude.",
                    "False.",
                    "L",
                    "I mean, I guess?",
                    "I mean, okay, sure.",
                    "Maybe.",
                    "I unclaim this claim.",
                    "Oh am I just dumb?",
                    "I have not decided.",
                    "Ask again in a funny accent.",
                    "Suing for libel.",
                    "Gone, reduced to ashes.",
                    "Fine, I'll do it myself.",
                    "Good.",
                    "Excellent.",
                    "I don't think so.",
                    "I doubt it.",
                    "Not even close.",
                    "Ehh, probably would do more harm than good.",
                    "Haha jk...        Unless...?",
                    "That would be funny I think.",
                    "I mean whatever you say I guess.",
                    "Probably not.",
                    "Doubtful.",
                    "Oh true.",
                    "Hmm.",
                    "Ping AllenY and do whatever he says.",
                    "You can do both.",
                    "Blocked. That question was too stupid to continue conversation with you.",
                    "Nice.",
                    "We are comayors now.",
                    "That's what I'm saying!",
                    "Can you ask that in a different way?",
                    "Dumbass.",
                    "Is that supposed to be a congnizable sentence?"
                    ]
        await ctx.channel.send(random.choice(wordlist))
        
    @commands.command(pass_context=True)
    async def generatename(self, ctx):
        """Generates a custom minecraft username"""
        await ctx.channel.send("Random Minecraft name generator is creating your username...")
        await ctx.channel.trigger_typing()
        await asyncio.sleep(3)

        if random.randint(0, 20) != 1:
            await ctx.channel.send(
                "...please be patient, our state of the art algorithms are still processing your request...")
            await ctx.channel.trigger_typing()
            await asyncio.sleep(random.randint(5, 7))

            if random.randint(0, 3) == 3:
                await ctx.channel.send(
                    "...your request was computationally intensive and requires additional processing...")
                await ctx.channel.trigger_typing()
                await asyncio.sleep(random.randint(7, 12))

        await ctx.channel.send("Your username is **minemaster" + str(random.randint(100, 999)) + "**")

    @commands.command(pass_context=True)
    async def pplocate(self, ctx, *, content):
        """Locates a players pearl"""
        with open('resources/pearl locations.txt', 'r') as file:
            locations = json.load(file)
        if content.lower() in locations:
            await ctx.channel.send(locations[content])
        else:
            await ctx.channel.send("**" + escape_mentions(content) + "**'s pearl could not be located")
   
    @commands.command(pass_context=True)
    async def election(self, ctx, content):
        newM = content
        try:
            newM = newM + " is the new 'mayor' of Mount September."
            await ctx.channel.send(newM)
        except:
            newM = str(newM)
            newM = newM + " is the new 'mayor' of Mount September."
            await ctx.channel.send(newM)
    

            
    @commands.command(pass_context=True, brief="Frees a players pearl")
    async def ppfree(self, ctx, *, content):
        """`ppfree <playername>`"""
        with open('resources/pearl locations.txt', 'r') as file:
            locations = json.load(file)
        if content.lower() in locations:
            await ctx.channel.send("You freed **" + escape_mentions(content) + "**")
            del locations[content.lower()]
            with open('resources/pearl locations.txt', 'w') as file:
                json.dump(locations, file)


def setup(bot):
    bot.add_cog(TextMeme(bot))

# todo : Disabled as perchance.py needs tweaks to use funfact
# perchance_fun_fact = perchance_parse(open('resources/perchance_funfact.txt').read())
# @bot.command(pass_context=True)
# async def funfact(ctx):
#     """Generates a CivClassic funfact"""
#     await ctx.channel.send(perchance_gen(perchance_fun_fact))
