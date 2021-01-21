from pathlib import Path

import discord
import yaml
from discord.ext import commands
from pymongo import MongoClient

# Set up config file and load
config_file = Path('MemberSignup\\config.yaml')

with open(config_file, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

connection = MongoClient(config['dbServer'], config['port'])


# Define bot class
class MemberSignup(commands.AutoShardedBot):
    def __init__(self, prefix, **options):
        super(MemberSignup, self).__init__(prefix, **options)


# Define privileged gateway intents

intents = discord.Intents.default()
intents.members = True  # Subscribe to the privileged members intent.

# Define bot and prefix
pre = config['prefix']
bot = MemberSignup(prefix=pre, case_insensitive=True, intents=intents, activity=discord.Activity(name=f'{pre}help'))
bot.config = config
bot.gdb = connection[config['guildDb']]


def main():
    """Tries to load every cog and start up the bot"""
    for extension in bot.config['load_extensions']:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension: {extension}')
            print('{}: {}'.format(type(e).__name__, e))

    print('MemberSignup is online.')
    bot.run(bot.config['token'], bot=True)


if __name__ == '__main__':
    main()
