import discord
from discord.ext import commands
from discord.utils import get, find
from discord.ext.commands import Cog, command

from ..utilities.supportFunctions import delete_command, strip_id, parse_list


class Signup(Cog):
    """Manages member signups on posts."""

    def __init__(self, bot):
        self.bot = bot
        global gdb
        gdb = bot.gdb

    # --- Listeners ---

    def update_embed(self, post):
        guild_id = post['guildId']
        message_id = post['messageId']
        title = post['title']
        body = post['body']
        members = post['members']

        if members:
            mapped_members = list(map(str, members))
            formatted_members = '- <@!' + '>\n- <@!'.join(mapped_members) + '>'

        post_embed = discord.Embed(title=title, type='rich', description=body)
        post_embed.add_field(name=f'Users:', value=formatted_members)

        return post_embed


def setup(bot):
    bot.add_cog(Signup(bot))
