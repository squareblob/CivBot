import asyncio
import json
import os
import pickle
import pprint
import re
from collections import defaultdict

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


async def find_discord_invite(my_channel, id):
    try:
        with open('resources/discord_data.json', 'r') as file:
            discord_data = json.load(file)
    except json.decoder.JSONDecodeError as e:
        print(e)

    discord_invite = None
    view_invite_perms = my_channel.guild.get_member(id).permissions_in(my_channel).manage_guild
    if view_invite_perms:
        try:
            inv = await my_channel.invites()
        except Exception as e:
            print(e)
        else:
            for s in inv:
                if s.max_age == 0 or s.max_age > (12 * 60 * 60):
                    discord_invite = "https://discord.gg/" + str(s.code)
                    break

        create_invite_perms = my_channel.guild.get_member(id).permissions_in(my_channel).create_instant_invite
        if create_invite_perms and discord_invite is None:
            try:
                discord_invite = await my_channel.create_invite(max_age=24 * 60 * 60)
                discord_invite = "https://discord.gg/" + str(discord_invite.code)
            except Exception as e:
                print(e)

    if discord_invite is None and discord_data is not None:
        if my_channel.guild.id in discord_data.keys():
            if len(discord_data[my_channel.guild.id]['valid_invites']) > 0:
                discord_invite = discord_data[my_channel.guild.id]['valid_invites'][0]

    return discord_invite


class VoiceRelayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @has_permissions(manage_channels=True)
    async def selectvoicechannels(self, ctx):
        """Selects which voice channels to relay member amount of. Defaults to none, requires `manage_channels` permission."""
        try:
            with open('resources/relayconfig.json', 'r') as file:
                guilds = json.load(file)
        except json.decoder.JSONDecodeError:
            pass

        guilds = defaultdict(dict, guilds)
        guilds[str(ctx.guild.id)] = defaultdict(list, guilds[str(ctx.guild.id)])
        channels_relayed = guilds[str(ctx.guild.id)]['channels_relayed']

        def check_author(message):
            return message.author == ctx.message.author

        await ctx.channel.send("Will display a list of all voice channels in guild in UI order from top to bottom. Type `confirm` to continue")
        try:
            msg = await self.bot.wait_for('message', timeout=7, check=check_author)
            if msg.content in ["confirm", "c"]:
                output = "```"
                category_ids = []

                for x in range(0, len(ctx.guild.voice_channels)):
                    if ctx.guild.voice_channels[x].category_id and ctx.guild.voice_channels[x].category_id not in category_ids:
                        output += "\n  ---" + str(ctx.guild.voice_channels[x].category.name) + "---  "
                        category_ids.append(ctx.guild.voice_channels[x].category_id)

                    output += "\n" + str(x + 1) + ") " + ctx.guild.voice_channels[x].name.ljust(50)
                    if ctx.guild.voice_channels[x].id in channels_relayed:
                        output += " [Currently relayed]"
                    has_view_perms = ctx.guild.get_member(self.bot.user.id).permissions_in(ctx.guild.voice_channels[x]).read_messages
                    if not has_view_perms:
                        output += " [Bot does not have perms to view]"

                await ctx.channel.send(
                    output + "```" + "Select a channel number or comma seperated list of channel numbers. Prefix a number with `^` to remove an already set channel from relay")
                try:
                    msg = await self.bot.wait_for('message', timeout=20, check=check_author)
                except asyncio.TimeoutError:
                    await ctx.channel.send(":x: Timed out")
                else:
                    for x in msg.content.split(","):
                        if re.match("\^?\d+", x) and 1 <= int(x.replace('^', '')) < len(ctx.guild.voice_channels) + 1:
                            if '^' in x:
                                channels_relayed = list(filter(lambda a: a != ctx.guild.voice_channels[int(x.replace('^', '')) - 1].id, channels_relayed))
                            else:
                                if ctx.guild.voice_channels not in channels_relayed:
                                    channels_relayed.append(ctx.guild.voice_channels[int(x.replace('^', '')) - 1].id)

                    guilds[str(ctx.guild.id)]['channels_relayed'] = channels_relayed

                    with open('resources/relayconfig.json', 'w') as file:
                        json.dump(guilds, file)
                    await ctx.channel.send(
                        "Channel relays updated. Remember that I need permission to join voice channel in order to relay")
            else:
                ctx.channel.send(":x:No voice channels could be found")
        except asyncio.TimeoutError:
            await ctx.channel.send(":x: Timed out")

    @commands.command(pass_context=True)
    @has_permissions(manage_channels=True)
    async def voicerelay(self, ctx, arg):
        """`create` or `remove` a Voice Relay Dashboard from the current channel"""
        # To do : This should be subcommands (or something)
        if arg == "create" or arg == "remove":
            try:
                with open('resources/relayconfig.json', 'r') as file:
                    guilds = json.load(file)
            except json.decoder.JSONDecodeError:
                pass
            guilds = defaultdict(dict, guilds)
            guilds[str(ctx.guild.id)] = defaultdict(list, guilds[str(ctx.guild.id)])

            relay_channels = [l['channel_id'] for l in guilds[str(ctx.guild.id)]['view_relay_channels']]
            if arg == "create" and ctx.channel.id not in relay_channels:
                guilds[str(ctx.guild.id)]['view_relay_channels'].append({"channel_id": ctx.channel.id})
            elif arg == "remove" and ctx.channel.id in relay_channels:
                for t in range(0, len(guilds[str(ctx.guild.id)]['view_relay_channels'])):
                    if guilds[str(ctx.guild.id)]['view_relay_channels'][t]["channel_id"] == ctx.channel.id:
                        guilds[str(ctx.guild.id)]['view_relay_channels'].pop(t)
                # To do : on removal, wipe removed dashboard.

            with open('resources/relayconfig.json', 'w') as file:
                json.dump(guilds, file)
            await ctx.channel.send("Channel relays updated")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        current_vc_data = []
        try:
            with open('resources/relayconfig.json', 'r') as file:
                guilds_json = json.load(file)
        except json.decoder.JSONDecodeError as e:
            print(e)
        try:
            with open('resources/VC_temp_storage.pickle', 'rb') as handle:
                current_vc_data = pickle.load(handle)
        except Exception as e:
            print(e)

        if before.channel != after.channel and guilds_json is not None:
            for guild_id in guilds_json.keys():
                if 'channels_relayed' in guilds_json[guild_id].keys():
                    channels = []
                    if before.channel is not None and before.channel.id in guilds_json[guild_id]["channels_relayed"]:
                        channels.append(before.channel)
                    if after.channel is not None and after.channel.id in guilds_json[guild_id]["channels_relayed"]:
                        channels.append(after.channel)

                    for VC in channels:
                        VC_info = {
                            "count": len(VC.members),
                            "vc_name": VC.name,
                            "vc_id": VC.id,
                            "guild_name": self.bot.get_guild(int(guild_id)).name,
                            "guild_id": guild_id,
                            "discord": await find_discord_invite(VC, self.bot.user.id)
                        }

                        for i in range(0, len(current_vc_data)):
                            if current_vc_data[i]['vc_id'] == VC.id:
                                if len(VC.members) != 0:
                                    current_vc_data[i] = VC_info
                                else:
                                    current_vc_data.pop(i)
                        if len(VC.members) != 0 and VC_info not in current_vc_data:
                            current_vc_data.append(VC_info)

            VC_relay_message = "**Civ Voice Chat Dashboard**"
            for vc in current_vc_data:
                VC_relay_message += "\n**" + str(vc["count"]) + "** users are in `" + vc["guild_name"] + "`::`" + vc["vc_name"] + "`\n"
                if vc["discord"] is not None:
                    VC_relay_message += vc["discord"]

            for guild_id in guilds_json.keys():
                # To do : make a default dict or something
                if 'view_relay_channels' in guilds_json[guild_id].keys():
                    for j in range(0, len(guilds_json[guild_id]['view_relay_channels'])):
                        try:
                            channel_to_send_in = self.bot.get_channel(int(guilds_json[guild_id]['view_relay_channels'][j]['channel_id']))

                            if channel_to_send_in is not None:
                                if 'message_id' in guilds_json[guild_id]['view_relay_channels'][j].keys() and guilds_json[guild_id]['view_relay_channels'][j]['message_id'] is not None:
                                    await (await channel_to_send_in.fetch_message(guilds_json[guild_id]['view_relay_channels'][j]['message_id'])).edit(content=VC_relay_message)
                                else:
                                    msg_to_store = await channel_to_send_in.send(VC_relay_message)
                                    guilds_json[guild_id]['view_relay_channels'][j]['message_id'] = msg_to_store.id
                        except Exception as e:
                            print(e)

            with open('resources/relayconfig.json', 'w') as file:
                json.dump(guilds_json, file)
            with open('resources/VC_temp_storage.pickle', 'wb') as handle:
                pickle.dump(current_vc_data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def setup(bot):
    bot.add_cog(VoiceRelayCog(bot))
