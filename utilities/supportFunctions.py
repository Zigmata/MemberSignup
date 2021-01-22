import re

import discord
from discord.ext import commands


# Deletes command invocations
async def delete_command(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass


# Verifies the user that invokes a command has a
# server-defined GM role
def has_gm_role():
    async def predicate(ctx):
        gdb = ctx.bot.gdb
        collection = gdb['gm_roles']
        guild_id = ctx.guild.id

        query = collection.find_one({'guild_id': guild_id})
        if query:
            gm_roles = query['gm_roles']
            for role in ctx.author.roles:
                if role.id in gm_roles:
                    return True

        await delete_command(ctx.message)
        raise commands.CheckFailure("You do not have permissions to run this command!")

    return commands.check(predicate)


def strip_id(mention) -> int:
    stripped_mention = re.sub(r'[<>#!@&]', '', mention)
    parsed_id = int(stripped_mention)
    return parsed_id


def parse_list(mentions) -> [int]:
    stripped_list = [re.sub(r'[<>#!@&]', '', item) for item in mentions]
    mapped_list = list(map(int, stripped_list))
    return mapped_list
