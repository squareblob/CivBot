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