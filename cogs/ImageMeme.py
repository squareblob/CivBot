import asyncio
import datetime
import io
import math
import random
import string
import re
import json
import functools
import uuid

import aiofiles
import aiohttp
import requests
import discord
from os import path
from mcuuid.api import GetPlayerData
from PIL import Image, ImageDraw, ImageFont, ImageOps

from discord.ext import commands

# -----------
# Draw images
# -----------


def draw_pearl_image(pearled_player, pearled_by, now):
    random.seed(a=pearled_player.lower() + pearled_by.lower() + now, version=2)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    font = ImageFont.truetype("resources/fonts/Minecraftia.ttf", 24)
    font_italic = ImageFont.truetype("resources/fonts/Minecraft-Italic.otf", 30)
    im = Image.open("resources/ImageMeme/Pearl_template.png")

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


def draw_joinedweezer_image(players):
    to_send = []
    drawn_players = ["", "", "", ""]
    joiners = ""
    rect_corners = [
        [(3, 300), (78, 94)],
        [(78, 300), (148, 107)],
        [(153, 300), (222, 94)],
        [(226, 300), (294, 100)]
    ]
    background = Image.open("resources/ImageMeme/Weezer_template.png")
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
                player_to_paste = Image.open("resources/test.png")
                background.paste(player_to_paste, (rect_corners[x][0][0], rect_corners[x][1][1]),
                                 mask=player_to_paste)
                joiners += ", " + drawn_players[x]
        background.save('resources/output.png', "PNG")
        if sum([x != "" for x in drawn_players]) > 1:
            k = joiners.rfind(", ")
            joiners = joiners[:k] + " and" + joiners[k + 1:]

        out_2 = "**Oh my God" + joiners + " joined weezer!**"
    return to_send, out_2


def draw_derelict_image(input_string):
    background = Image.open("resources/output.png")
    sign = Image.open("resources/ImageMeme/Sign_template.png")
    for i in range(0, len(input_string)):
        font = ImageFont.truetype("resources/fonts/Minecraftia.ttf", 42 - (i * 2))
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


def draw_getalong_image(players):
    img_shirt = Image.open("resources/ImageMeme/shirt.png")
    background = Image.new('RGB', (600, 500), color=(255, 255, 255))
    for i, player in enumerate(players):
        r = requests.get("https://mc-heads.net/player/" + player + "/160.png")
        background.paste(Image.open(io.BytesIO(r.content)), ((150 + i * 150), (110 - i * 12)))
    background.paste(img_shirt, (0, 0), mask=img_shirt)
    background.save('resources/output.png', "PNG")


def draw_dontcare_image(username):
    r = requests.get("https://mc-heads.net/avatar/" + str(username) + "/325.png")

    with open("resources/test.png", 'wb') as f:
        f.write(r.content)

    temp = Image.open("resources/test.png")

    half_area = (0, 0, temp.height / 2, temp.width)
    new = temp.crop(half_area)

    new_image = Image.new('RGB', (temp.height, temp.width))
    new_image.paste(new)
    flip = ImageOps.mirror(new)
    new_image.paste(flip, (int(temp.width / 2), 0))

    upper = Image.open("resources/ImageMeme/Dontcare_template.png")
    new_image = new_image.convert('RGBA')
    new_image.paste(upper, (0, 0), upper.convert('RGBA'))
    new_image.save('resources/output.png', "PNG")


def draw_grimreminder_image(player):
    background = Image.open("resources/ImageMeme/grimreminder.jpg")
    r = requests.get("https://mc-heads.net/avatar/" + player + "/254.png")
    head = Image.open(io.BytesIO(r.content)).convert('RGBA')
    head = head.rotate(-12, Image.NEAREST, True, fillcolor=2)
    background.paste(head, (215, 372), head)
    background.save('resources/output.png', "PNG")


def draw_step_image(number):
    img_background = Image.open("resources/ImageMeme/oil_template.png")
    draw = ImageDraw.Draw(img_background)
    font = ImageFont.truetype("resources/fonts/NotoSans-Bold.ttf", 30)
    draw.text((40, 0), str(number) + ") cover yourself in oil", (30, 30, 30), font=font)
    img_background.save('resources/output.png', "PNG")


def draw_verb_at_image(filepath):
    inner = Image.open("resources/output.png")
    outer = Image.open(filepath)
    input_im = inner.resize((415, 415))
    newImage = Image.new('RGB', (outer.width, outer.height))
    newImage.paste(input_im, (54, 37))
    newImage.paste(outer, (0, 0), outer)
    newImage.save('resources/output.png', "PNG")


def draw_greyscale_image():
    inner = Image.open("resources/output.png").convert('L')
    inner.save('resources/output.png', "PNG")


def draw_chart_image(chart_data, chart_code):
    x_axis = chart_data[str(chart_code)]["x_axis"]
    y_axis = chart_data[str(chart_code)]["y_axis"]

    # DRAW TEXT
    background = Image.open("resources/ImageMeme/Chart/grid2500.png")
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

# -------
# helpers
# -------


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


class ImageMeme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------
    # Commands
    # --------

    @commands.command(pass_context=True)
    async def pearl(self, ctx, *, content):
        """Pearls a player"""
        if len(content.split(" ")) > 1:
            players = []
            for p in content.split(" ")[:2]:
                if GetPlayerData(p) and hasattr(GetPlayerData(p), 'username'):
                    players.append(GetPlayerData(p).username)
                elif not re.match('^(\w|d){3,16}', p):
                    await ctx.channel.send("Invalid usernames supplied")
                    return
                else:
                    players.append(re.match('^(\w|d){3,30}', p).group(0))

            date = datetime.datetime.today().strftime('%m/%d/%Y')
            if len(content.split(" ")) > 2 and re.match("\d{1,2}\/\d{1,2}\/\d{1,4}", content.split(" ")[2]):
                date = re.match("\d{1,2}\/\d{1,2}\/\d{1,4}", content.split(" ")[2]).group(0)

            params = functools.partial(draw_pearl_image, players[0], players[1], date)
            await self.bot.loop.run_in_executor(None, params)
            bot_message = await ctx.channel.send(file=discord.File("resources/output.png"))

            with open('resources/pearl locations.txt', 'r') as file:
                locations = json.load(file)
            await asyncio.sleep(1)
            locations[players[0].lower()] = bot_message.jump_url
            with open('resources/pearl locations.txt', 'w') as file:
                json.dump(locations, file)

    @commands.command(pass_context=True)
    async def joinedweezer(self, ctx, *args):
        """Let your minecraft avatar join Weezer"""
        params = functools.partial(draw_joinedweezer_image, list(args))
        msgs, image = await self.bot.loop.run_in_executor(None, params)
        for x in msgs:
            await ctx.channel.send(x)
        if image is not None:
            await ctx.channel.send(image, file=discord.File('resources/output.png'))

    @commands.command(pass_context=True)
    async def derelict(self, ctx, *args):
        """Derelicts an image"""
        result = await find_a_posted_image(ctx)
        if result is not None:
            if str(args) != "()":
                input_string = args[:4]
            else:
                input_string = ['DERELICTION', ctx.message.author.display_name,
                                datetime.datetime.today().strftime('%m/%d/%Y')]
            allowed_chars = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'abcdefghijklmnopqrstuvwxyz{|}~⌂ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜø£Ø×ƒáíóúñÑªº¿®¬½¼¡«»"
            for v in range(0, len(input_string)):
                for char in list(input_string[v]):
                    if char not in allowed_chars:
                        input_string[v] = input_string[v].replace(char, '')

            params = functools.partial(draw_derelict_image, input_string)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))

    @commands.command(pass_context=True)
    async def getalong(self, ctx, player1, player2):
        """Draws two players in the 'get along' shirt"""
        players = [player1, player2]
        for x in players:
            if not GetPlayerData(x).valid:
                await ctx.channel.send(
                    discord.utils.escape_markdown(discord.utils.escape_mentions(
                        x)) + " does not appear to be a valid player. Are you sure you typed correctly?")
                return
        params = functools.partial(draw_getalong_image, players)
        await self.bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))

    @commands.command(pass_context=True)
    async def dontcare(self, ctx, content):
        """Shows everyone how little you care"""
        if not GetPlayerData(content).valid:
            await ctx.channel.send(
                discord.utils.escape_markdown(discord.utils.escape_mentions(
                    content)) + " does not appear to be a valid player. Are you sure you typed correctly?")
        else:
            params = functools.partial(draw_dontcare_image, content)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File("resources/output.png"))

    @commands.command(pass_context=True)
    async def grimreminder(self, ctx, player):
        """Draws a grim reminder"""
        if not GetPlayerData(player).valid:
            await ctx.channel.send(
                discord.utils.escape_markdown(discord.utils.escape_mentions(
                    player)) + " does not appear to be a valid player. Are you sure you typed correctly?")
            return
        params = functools.partial(draw_grimreminder_image, player)
        await self.bot.loop.run_in_executor(None, params)
        await ctx.channel.send(file=discord.File('resources/output.png'))

    @commands.command(pass_context=True)
    async def step(self, ctx, number):
        """Draws the current step"""
        try:
            number = int(number)
            if number < 0 or number > 99999:
                await ctx.channel.send("Must be an integer between 0 and 99999")
                return
            params = functools.partial(draw_step_image, number)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))
        except ValueError:
            await ctx.channel.send("Must be an integer")

    @commands.command(pass_context=True)
    async def cryat(self, ctx, *args):
        """Crys at the image"""
        await self.verb_at_image(ctx, "resources/ImageMeme/Cry_template.png")

    @commands.command(pass_context=True)
    async def laughat(self, ctx, *args):
        """Laughs at the image"""
        await self.verb_at_image(ctx, "resources/ImageMeme/Laugh_template.png")

    @commands.command(pass_context=True)
    async def grey(self, ctx):
        """Makes an image greyscale"""
        result = await find_a_posted_image(ctx)
        if result is not None:
            params = functools.partial(draw_greyscale_image)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))

    @commands.command(pass_context=True)
    async def animemer(self, ctx):
        """returns the animemer codex"""
        await ctx.channel.send(file=discord.File('resources/ImageMeme/Animemer_template.png'))

    @commands.command(pass_context=True)
    async def entente(self, ctx):
        """Responds to an entente player"""
        await ctx.channel.send(file=discord.File('resources/ImageMeme/entente.png'))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(pass_context=True)
    async def nato(self, ctx):
        """Responds to a NATO player"""
        await ctx.channel.send(file=discord.File('resources/ImageMeme/NATO.png'))
        try:
            await ctx.message.delete()
        except:
            pass

    # ------
    # chart commands
    # ------

    @commands.group()
    async def chart(self, ctx):
        """Create x,y charts with Minecraft faces"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed...\nOptions include `view`,`edit`,`create`')

    @chart.command()
    async def view(self, ctx, chart_code):
        """Views a saved chart"""
        with open("resources/ImageMeme/Chart/chart_creator.txt") as json_file:
            chart_data = json.load(json_file)
        if str(chart_code) in chart_data.keys():
            params = functools.partial(draw_chart_image, chart_data, chart_code)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))

    @chart.command()
    async def edit(self, ctx, chart_code, playername, xpos, ypos):
        """Edits a chart with given chart code, Minecraft username, x coord and y coord."""
        with open("resources/ImageMeme/Chart/chart_creator.txt") as json_file:
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

            with open("resources/ImageMeme/Chart/chart_creator.txt", "w") as json_file:
                json.dump(chart_data, json_file)

            # optional : show chart after posting
            params = functools.partial(draw_chart_image, chart_data, chart_code)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))
        else:
            await ctx.send("chart not found")
        # make create chart method, view

    @chart.command()
    async def create(self, ctx, chart_name):
        """Creates a chart with given chart name"""
        with open("resources/ImageMeme/Chart/chart_creator.txt") as json_file:
            chart_data = json.load(json_file)

        await ctx.send('Name X-axis:')

        def pred(m):
            return m.author == ctx.author and m.channel == ctx.channel

        x_axis = await self.bot.wait_for('message', check=pred, timeout=60.0)
        await ctx.send('Name Y-axis:')
        y_axis = await self.bot.wait_for('message', check=pred, timeout=60.0)

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

        with open("resources/ImageMeme/Chart/chart_creator.txt", "w") as json_file:
            json.dump(chart_data, json_file)
        await ctx.send(':white_check_mark: Chart created. Chart can be accessed with the code ' + str(chart_id))

    # -------
    # Helpers
    # -------

    async def verb_at_image(self, ctx, location):
        result = await find_a_posted_image(ctx)
        if result is not None:
            params = functools.partial(draw_verb_at_image, location)
            await self.bot.loop.run_in_executor(None, params)
            await ctx.channel.send(file=discord.File('resources/output.png'))


def setup(bot):
    bot.add_cog(ImageMeme(bot))
