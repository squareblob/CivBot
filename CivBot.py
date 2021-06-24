import configparser
import os
import re
import time
import discord
from discord.ext import commands


prefix = "%"
bot = commands.Bot(command_prefix=prefix, description="CivBot", help_command=None)

gnu_linux = """
I'd just like to interject for a moment. What you're referring to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell utilities and vital system components comprising a full OS as defined by POSIX.

Many computer users run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called "Linux", and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.

There really is a Linux, and these people are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called "Linux" distributions are really distributions of GNU/Linux.
""".strip()
do_orange_response = False
# cut down on spam: don't respond if last response was recent
last_times = {}


@bot.command(pass_context=True)
async def invite(ctx):
    """CivBot invite"""
    await ctx.channel.send("https://discordapp.com/api/oauth2/authorize?client_id=614086832245964808&permissions=0&scope=bot")


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
                    MiscUtilities = bot.get_cog('MiscUtilities')
                    if MiscUtilities is not None:
                        await MiscUtilities.whereis(ctx, coords.group(1), coords.group(2), True)
                elif match_relay_chat_command.group(2) == "%drama": # set temporarily as somehow broken
                    TextMeme = bot.get_cog('TextMeme')
                    if TextMeme is not None:
                        await TextMeme.drama(ctx)
                else:
                    print(ctx.content)
                    await bot.process_commands(ctx)
            else:  # regular chat message
                lower_content = ctx.content.lower()
                if 'delusional' in lower_content:
                    await ctx.channel.send("Edit CivWiki <https://civwiki.org/wiki/CivWiki:Editing_Guide>")
                if 'lusitanian' in lower_content:
                    await ctx.channel.send(file=discord.File('resources/ImageMeme/Lusitan.png'))
                if 'his final message' in lower_content:
                    await ctx.channel.send("To live as a septembrian, is to embrace death.")
                if 'linux' in lower_content and not 'gnu' in lower_content and 60 > time.time() - last_times.get('gnu_linux', 0):
                    last_times['gnu_linux'] = time.time()
                    await ctx.channel.send(gnu_linux)

                match_page = "\[{2}([^\]\n]+) *\]{2}"
                match_template = "\{{2}([^\]\n]+) *\}{2}"

                wiki_message = ""
                wiki_link = "https://civwiki.org/wiki/"

                pages = list(set(re.findall(match_page, ctx.content)))
                templates = list(set(re.findall(match_template, ctx.content)))
                for template in templates:
                    pages.append("Template:" + template)
                for page in pages[:10]:
                    wiki_message += wiki_link + page.replace(" ", "_") + "\n"
                if len(pages) > 0:
                    await ctx.channel.send(wiki_message)
            if len(ctx.attachments) != 0:
                for x in ctx.attachments:
                    if os.path.splitext(x.filename)[1] == ".schematic" or os.path.splitext(x.filename)[1] == ".schem":
                        MiscUtilities = bot.get_cog('MiscUtilities')
                        if MiscUtilities is not None:
                            await MiscUtilities.getschematic(ctx, x)
    except AttributeError:
        print("From " + str (ctx.author) + ": " + ctx.content)


@bot.event
async def on_ready():
    print("connected to discord")
    print("In " + str(len(bot.guilds)) + " guilds")
    for guild in bot.guilds:
        print("    " + guild.name)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('reddit.com/r/civclassics'))


extensions = [
    "ImageMeme",
    "TextMeme",
    "MiscUtilities",
    "CivDiscord"
]

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_type = 'auth'
    config.read('config.ini')
    token = config.get(config_type, 'token')

    for extension in extensions:
        bot.load_extension(f"cogs.{extension}")

    while True:
        try:
            bot.run(token)
        except Exception as e:
            print("Error", e)
        print("Waiting until restart")
        time.sleep(20)
