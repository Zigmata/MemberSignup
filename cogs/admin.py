import time

from discord.ext import commands
from discord.ext.commands import Cog, command
from discord.utils import find

from ..utilities.supportFunctions import delete_command


class Admin(Cog):
    """Administrative commands such as server configuration and bot options."""

    def __init__(self, bot):
        self.bot = bot
        global gdb
        gdb = bot.gdb

    # -------------Private Commands-------------

    # Reload a cog by name
    @commands.is_owner()
    @command(hidden=True)
    async def reload(self, ctx, module: str):
        self.bot.reload_extension('MemberSignup.cogs.' + module)
        await delete_command(ctx.message)

        msg = await ctx.send('Extension successfully reloaded: `{}`'.format(module))
        time.sleep(3)
        await msg.delete()

    # Loads a cog that hasn't yet been loaded
    @commands.is_owner()
    @command(hidden=True)
    async def load(self, ctx, module: str):
        self.bot.load_extension('MemberSignup.cogs.' + module)

        msg = await ctx.send('Extension successfully loaded: `{}`'.format(module))
        time.sleep(3)
        await msg.delete()

        await delete_command(ctx.message)

    # Shut down the bot
    @commands.is_owner()
    @command(hidden=True)
    async def shutdown(self, ctx):
        try:
            await ctx.send('Shutting down!')
            await delete_command(ctx.message)
            await ctx.bot.logout()
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))

    # -------------Config Commands--------------

    @commands.has_guild_permissions(manage_guild=True)
    @commands.group(aliases=['conf'], case_insensitive=True, pass_context=True)
    async def config(self, ctx):
        """Commands for server configuration of bot options and features."""
        if ctx.invoked_subcommand is None:
            return

    # --- Role ---

    @config.group(case_insensitive=True, pass_context=True)
    async def role(self, ctx):
        """Commands for configuring roles for various features."""
        if ctx.invoked_subcommand is None:
            return

    @role.group(case_insensitive=True, pass_context=True, invoke_without_command=True)
    async def staff(self, ctx):
        """
        Sets the staff role(s), used for staff commands.

        When this base command is executed, it displays the current setting.
        """
        guild_id = ctx.message.guild.id
        guild = self.bot.get_guild(guild_id)
        collection = gdb['staffRoles']

        query = collection.find_one({'guildId': guild_id})
        if not query or not query['staffRoles']:
            await ctx.send('staff role(s) not set! Configure with '
                           '`{}staffRole <role mention>`. Roles can be chained (separate with a space).'.format(
                self.bot.command_prefix))
        else:
            current_roles = query['staffRoles']
            role_names = []
            for id in current_roles:
                role_names.append(guild.get_role(id).name)

            await ctx.send('staff Role(s): {}'.format('`' + '`, `'.join(role_names) + '`'))

        await delete_command(ctx.message)

    @staff.command(aliases=['a'], pass_context=True)
    async def add(self, ctx, *roles):
        """
        Adds a role to the staff list.

        Arguments:
        [role name]: Adds the role to the staff list. Roles with spaces must be encapsulated in quotes.
        """

        guild_id = ctx.message.guild.id
        collection = gdb['staffRoles']

        if roles:
            guild = self.bot.get_guild(guild_id)
            query = collection.find_one({'guildId': guild_id})
            new_roles = []

            # Compare each provided role name to the list of guild roles
            for role in roles:
                search = find(lambda r: r.name.lower() == role.lower(), guild.roles)
                if search:
                    new_roles.append(search.id)

            if not new_roles:
                await ctx.send('Role not found! Check your spelling and use of quotes!')
                await delete_command(ctx.message)
                return

            if query:
                # If a document exists, check to see if the id of the provided role is already set
                staff_roles = query['staffRoles']
                for new_id in new_roles:
                    if new_id in staff_roles:
                        continue
                    else:
                        # If there is no match, add the id to the database
                        collection.update_one({'guildId': guild_id}, {'$push': {'staffRoles': new_id}})

                # Get the updated document
                update_query = collection.find_one({'guildId': guild_id})['staffRoles']

                # Get the name of the role matching each ID in the database, and output them.
                role_names = []
                for id in update_query:
                    role_names.append(guild.get_role(id).name)
                await ctx.send('staff role(s) set to {}'.format('`' + '`, `'.join(role_names) + '`'))
            else:
                # If there is no document, create one with the list of role IDs
                collection.insert_one({'guildId': guild_id, 'staffRoles': new_roles})
                role_names = []
                for id in new_roles:
                    role_names.append(guild.get_role(id).name)
                await ctx.send('Role(s) {} added as staffs'.format('`' + '`, `'.join(role_names) + '`'))
        else:
            await ctx.send('Role not provided!')

        await delete_command(ctx.message)

    @staff.command(aliases=['r'], pass_context=True)
    async def remove(self, ctx, *roles):
        """
        Removes existing staff roles.

        Arguments:
        [role name]: Removes the role from the staff list. Roles with spaces must be encapsulated in quotes.
        --<all>: Removes all roles from the staff list.
        """

        guild_id = ctx.message.guild.id
        guild = self.bot.get_guild(guild_id)
        collection = gdb['staffRoles']

        if roles:
            if roles[0] == 'all':  # If 'all' is provided, delete the whole document
                query = collection.find_one({'guildId': guild_id})
                if query:
                    collection.delete_one({'guildId': guild_id})

                await ctx.send('staff roles cleared!')
            else:
                # Get the current list of roles (if any)
                query = collection.find_one({'guildId': guild_id})

                # If there are none, inform the caller.
                if not query or not query['staffRoles']:
                    await ctx.send('No staff roles are configured!')
                # Otherwise, build a list of the role IDs to delete from the database
                else:
                    role_ids = []
                    for role in roles:
                        # find() will end at the first match in the iterable
                        search = find(lambda r: r.name.lower() == role.lower(), guild.roles)
                        if search:  # If a match is found, add the id to the list
                            role_ids.append(search.id)

                    # If the list is empty, notify the user there were no matches.
                    if not role_ids:
                        await ctx.send('Role not found! Check your spelling and use of quotes!')
                        await delete_command(ctx.message)
                        return

                    current_roles = query['staffRoles']
                    # Build the set where provided roles exist in the db
                    deleted_roles = set(role_ids).intersection(current_roles)
                    for role in deleted_roles:
                        collection.update_one({'guildId': guild_id}, {'$pull': {'staffRoles': role}})

                    # Fetch the updated document
                    update_query = collection.find_one({'guildId': guild_id})['staffRoles']
                    if update_query:
                        updated_roles = []
                        for id in update_query:
                            for role in guild.roles:
                                if id == role.id:
                                    updated_roles.append(role.name)
                        await ctx.send('staff role(s) set to {}'.format('`' + '`, `'.join(updated_roles) + '`'))
                    else:
                        await ctx.send('staff role(s) cleared!')
        else:
            await ctx.send('Role not provided!')

        await delete_command(ctx.message)


def setup(bot):
    bot.add_cog(Admin(bot))
