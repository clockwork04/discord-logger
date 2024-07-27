from datetime import datetime, timezone, timedelta
import logging

import discord
from discord.ext import commands

import config.settings
from ext import database, embeds, functions

logger = logging.getLogger(name='WGEDLA')

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)

class MessageLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # How to handle attachments, stickers, external emojis
    # when checking for mod deletion, match message id not author/channel ids
    # break listeners to separate functions

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            return

        log_type = 'delete'
        if not functions.enabled_check(bot=self.bot, guild_id=message.guild.id, log_type=log_type, channel_id=message.channel.id):
            return

        if not self.pre_checks(message):
            return

        await database.database_insert_message(message)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not payload.guild_id:
            return

        log_type = 'delete'
        if not functions.enabled_check(bot=self.bot, guild_id=payload.guild_id, log_type=log_type, channel_id=payload.channel_id):
            return

        databaseMessage = False
        if payload.cached_message is None:
            message = await database.database_get_last_message(bot=self.bot, guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id)
            databaseMessage = True
        else:
            message = payload.cached_message
            databaseMessage = False
        
        timestamp = datetime.now(timezone.utc)
        debugDelta = (timestamp.replace(tzinfo=None) - message.created_at.replace(tzinfo=None))
        debugDelta = (debugDelta.seconds * 1000) + (debugDelta.microseconds / 1000)
        if debugDelta < config.settings.DELETE_COOLDOWN:
            logger.info(msg=f'Delay drop triggered! Delay:{debugDelta}ms User: {message.author} Location: {message.guild.id}/{message.channel.id}/{message.id}')
            return

        if not self.pre_checks(message):
            return

        if hasattr(message.author, 'id'):
            moderator = await self.get_moderator(message)   
        else:
            moderator = None

        #now, this might look insideous buuut, I can assure you this is just to negate PluralKit spam in WGE.
        if moderator:
            if str(moderator.id) in config.settings.OPERATOR_WHITELIST_IDS and config.settings.NSA_MODE is False:
                return

        # ERROR: message.channel = None
        # Union[TextChannel, StageChannel, VoiceChannel, Thread, DMChannel, GroupChannel, PartialMessageable]

        #Embed Builder
        embed = embeds.message_delete_log_extended(message, moderator, timestamp, databaseMessage)
        await self.send_log(payload.guild_id, log_type, embed)
        database.database_delete_message(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        if not payload.guild_id:
            return

        log_type = 'edit'
        if not functions.enabled_check(bot=self.bot, guild_id=payload.guild_id, log_type=log_type, channel_id=payload.channel_id):
            return

        try:
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not self.pre_checks(message):
            return

        ##Assuming message is loaded into memory after this  ~Snoopie
        if payload.cached_message is None:
            message_object = await database.database_get_last_message(bot=self.bot, guild_id=payload.guild_id, channel_id=payload.channel_id, message_id=payload.message_id)
            before = message_object.content
        else:
            before = payload.cached_message.content

        #Checking for message edit anomilies. ~Snoopie
        #this used to be critical but in production this happens so terrifically often logging them all to standard output seems stupid. ~Snoopie
        if (before == message.content) or (before == ""):
            logger.warning(msg=f'Edit anomily detected! Incident Location: {message.guild.id}/{message.channel.id}/{message.id}')
            return

        embed = embeds.message_edit_log_extended(message=message, before=before)
        await self.send_log(guild_id=payload.guild_id, log_type=log_type, embed=embed)
        await database.database_insert_message(message)

    async def get_moderator(self, message: discord.Message):
        moderator = None
        after = datetime.now(timezone.utc) - timedelta(seconds=5)
        if message.author is not None:
            async for entry in message.guild.audit_logs(after=after, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    moderator = entry.user
                    break
        return moderator

    async def send_log(self, guild_id: int, log_type: str, embed):
        channel_id = int(self.bot.guild_settings[guild_id][log_type]['channel_id'])
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            self.bot.logger.error('%s Log channel with ID %s not found', self.bot.guild_settings[guild_id][log_type], channel_id)
        if isinstance(embed, tuple):
            if embed[1] is not False: 
                await channel.send(embed=embed[0], file=embed[1])
            else: 
                await channel.send(embed=embed[0])
        else:
            await channel.send(embed=embed)
            

    def pre_checks(self, message: discord.Message):
        #See, where I'm from (Java) we have an operator called "!" and it makes this much less stupid, so I apologize. ~Snoopie
        if message.author.id in config.settings.USER_WHITELIST_IDS and config.settings.NSA_MODE is False:
            return
        
        if message.author.bot is True:
            return

        if message.guild is None:
            return

        if message.type != discord.MessageType.default and message.type != discord.MessageType.reply:
            return

        if not message.channel:
            return

        return True

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLog(bot))
