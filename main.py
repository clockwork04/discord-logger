import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

import config
from ext.functions import set_guild_invites

#comeonnn who can resist ascii art? ~Snoopie
brandingAArt = [f' _      ______________  __   ___ ', f'| | /| / / ___/ __/ _ \\/ /  / _ |', f'| |/ |/ / (_ / _// // / /__/ __ |', f'|__/|__/\\___/___/____/____/_/ |_|']

logger = logging.getLogger(name='WGEDLA')
logger.setLevel(logging.INFO)

fh = logging.FileHandler(filename='loggerlog.log')
fh.setLevel(logging.INFO)
fh.setFormatter((logging.Formatter('%(asctime)s %(levelname)-8s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')))
logger.addHandler(fh)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)

intents = discord.Intents.none()
intents.guild_messages = True
intents.guilds = True
intents.invites = True
intents.members = True
intents.message_content = True
intents.moderation = True
intents.voice_states = True

class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = config.settings.COMMAND_PREFIX,
            intents = intents,
            log_hander = logger,
            application_id = config.settings.APPLICATION_ID,
        )
        self.logger = logger
        self.synced = False # still needed?
        self.guild_settings = {}

    async def load_cog(self, directory, file):
        if file.endswith('.py'):
            try:
                await bot.load_extension(f'{directory}.{file[:-3]}')
                self.logger.info('Loaded extension %s.%s', directory, file[:-3])
            except discord.ext.commands.errors.NoEntryPointError:
                pass

    async def setup_hook(self):
        for string in brandingAArt:
            logger.warning(msg=string)

        #for better logfile readability. ~Snoopie
        logger.warning(msg='WGE Dedicated Logging Application is starting up!'),
        bot.remove_command('help')
        ignore_items = ['__pycache__']
        for item in os.listdir('cogs'):
            if item in ignore_items:
                continue

            if os.path.isdir(f'cogs/{item}'):
                for file in os.listdir(f'cogs/{item}'):
                    await self.load_cog(f'cogs.{item}', file)
            else:
                await self.load_cog('cogs', item)

    async def on_ready(self):
        await self.wait_until_ready()

        @bot.event
        async def on_message(message):
            if message.author == bot.user:
                return
            await bot.process_commands(message)

        @bot.check
        async def globally_block_dms(ctx):
            return ctx.guild is not None

        for guild in self.guilds:
            await set_guild_invites(self, guild)

        self.logger.warning('logged in as %s | %s', self.user.name, self.user.id)

bot = DiscordBot()

class LoggingHandler(logging.Handler):
    def __init__(self, stdout, discord_bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stdout = stdout
        self.bot = discord_bot

    async def send_log(self, record):
        log_entry = self.format(record)
        if 'We are being rate limited' not in str(record):
            if config.settings.DEV_CHANNEL:
                channel = self.bot.get_channel(config.settings.DEV_CHANNEL)
                if channel is None:
                    pass
                else:
                    await channel.send(f'```prolog\n{log_entry[:1800]}```')

    def emit(self, record):
        asyncio.ensure_future(self.send_log(record))
        self.stdout.write(self.format(record) + '\n')

logger_handler = LoggingHandler(sys.stdout, bot)
logger_handler.setLevel(logging.WARNING)
logger_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(logger_handler)

if __name__ == '__main__':
    bot.run(config.secrets.TOKEN)
