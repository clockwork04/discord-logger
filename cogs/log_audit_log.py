import discord
from discord.ext import commands

from ext import audit_log, functions, database


class AuditLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if not functions.guild_check(bot=self.bot, guild_id=entry.guild.id):
            return

        database.database_insert_audit_log_entry(entry=entry)
        await audit_log.log_audit_log_entry(self.bot, entry, self.bot.guild_settings[entry.guild.id]['audit'])

async def setup(bot: commands.Bot):
    await bot.add_cog(AuditLog(bot))
