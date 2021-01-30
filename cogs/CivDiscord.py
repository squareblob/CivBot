import json
import discord

from discord.ext import commands
from fuzzywuzzy import fuzz, process


class CivDiscord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def civdiscord(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed...')

    @civdiscord.command()
    async def add(self, ctx, content):
        """Adds a discord server invite to CivBot"""
        discord_data, invite = await self.check_invite(ctx, content)
        if discord_data is not None:
            inv_id = str(invite.guild.id)
            if inv_id not in discord_data.keys():
                discord_data[inv_id] = {}
                discord_data[inv_id]['valid_invites'] = [str(content)]
                discord_data[inv_id]['invalid_invites'] = []
                discord_data[inv_id]['current_name'] = str(invite.guild.name)
                discord_data[inv_id]['approximate_member_count'] = str(invite.approximate_member_count)
                with open('resources/CivDiscord/discord_data.json', 'w') as outfile:
                    json.dump(discord_data, outfile)
                await ctx.send("Added a new guild")
            else:
                if str(content) in discord_data[inv_id]['valid_invites']:
                    await ctx.send("This invite code has already been submitted")
                else:
                    discord_data[inv_id]['valid_invites'].append(str(content))
                    with open('resources/CivDiscord/discord_data.json', 'w') as outfile:
                        json.dump(discord_data, outfile)
                    await ctx.send("Invite code was successfully added")

    @civdiscord.command()
    async def nick(self, ctx, inv_code, name):
        """Adds a nickname to discord server entry"""
        try:
            discord_data, invite = await self.check_invite(ctx, inv_code)
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
                        with open('resources/CivDiscord/discord_data.json', 'w') as outfile:
                            json.dump(discord_data, outfile)
                        await ctx.send("Nickname was added")
        except FileNotFoundError as e:
            await ctx.send("Nickname must be in format \"invite_code nickname\"")

    @civdiscord.command()
    async def rate(self, ctx, inv_code, rating):
        """Rates a discord server"""
        try:
            discord_data, invite = await self.check_invite(ctx, inv_code)
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
                    if rating.isdigit() and 1 <= int(rating) <= 5:
                        rating = int(rating)
                        msg = ""
                        discord_data[inv_id]['rating'][str(ctx.author.id)] = rating
                        if old_rating is not None:
                            msg += "Old rating :" + ("".join([":star:" for x in range(0, int(old_rating))]) + (
                                '+' if old_rating > int(old_rating) + .4 else "")) + "\n"
                        msg += "Rating :" + ("".join([":star:" for x in range(0, int(rating))]) + (
                            '+' if rating > int(rating) + .4 else "")) + "\n"
                        with open('resources/CivDiscord/discord_data.json', 'w') as outfile:
                            json.dump(discord_data, outfile)
                        await ctx.send(msg)
                    else:
                        await ctx.send("Rating must be integer between 1 and 5 stars")
        except FileNotFoundError:
            await ctx.send("Nickname must be in format \"invite_code nickname\". Invite code must be valid")

    @civdiscord.command()
    async def search(self, ctx, content):
        """Search for a discord server invite stored by CivBot"""
        with open('resources/CivDiscord/discord_data.json') as json_file:
            discord_data = json.load(json_file)

        matches = []
        keys = []

        for key in discord_data:
            if 'current_name' in discord_data[key].keys():
                if len(content) > 4:
                    match = fuzz.token_set_ratio(content, discord_data[key]['current_name'])
                else:
                    match = fuzz.ratio(content, discord_data[key]['current_name'])
            if 'nickname' in discord_data[key].keys():
                test, match = process.extractOne(content, discord_data[key]['nickname'])
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
                    rating = rating / len(discord_data[keys[i]]["rating"])
                    stars = ("".join([":star:" for x in range(0, int(rating))]) + (
                        '+' if rating > int(rating) + .4 else ""))

                resp += discord_data[keys[i]]['valid_invites'][0] + (" " + stars if stars is not None else "") + "\n"

            await ctx.send(resp)
        else:
            await ctx.send("No matches could be found")

    # -------
    # helpers
    # -------

    async def check_invite(self, ctx, content):
        try:
            invite = await self.bot.fetch_invite(content)
            if invite is not None:
                with open('resources/CivDiscord/discord_data.json') as json_file:
                    discord_data = json.load(json_file)
                return discord_data, invite
        except discord.NotFound:
            await ctx.send("This is not a valid invite")
            return None


def setup(bot):
    bot.add_cog(CivDiscord(bot))
