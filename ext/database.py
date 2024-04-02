import asyncio
import logging
import discord
import urllib.request
from discord.ext import commands
from pymongo import DESCENDING, MongoClient
from PIL import Image

from config.secrets import MONGO_URI
from ext.audit_log import recursive_object_to_dict

logger = logging.getLogger(name='WGEDLA')

log_database = MongoClient(MONGO_URI)

#This wasnt async when I found it, but because attachment.save is async.. it is now.
#I'm sure I'll find out why it wasnt before soon enough x3 ~Snoopie
async def database_insert_message(message: discord.Message):
    if message.attachments:
        attachment = message.attachments[0]
        attachment0data = attachment.url + "//FILENAME//" + attachment.filename
        #Now that we have departed the second normal form the attachment we have a record of must be cached.
        #The idea is using asyncio should keep the rest of the code running while the attachment is downloading. ~Snoopie
        asyncio.create_task(attachmentCacher(attachment, message.id, attachment.filename))
    else:
        attachment0data = ""

    doc = {
        'message_id': str(message.id),
        'guild_id': str(message.guild.id),
        'channel_id': str(message.channel.id),
        'author': str(message.author),
        'author_id': str(message.author.id),
        'created_at': message.created_at,
        'content': message.content,
        'edited_at': message.edited_at,
        'deleted': False,
        'attachment0': str(attachment0data),
    }

    result = log_database[str(message.guild.id)][str(message.channel.id)].insert_one(doc)
    if result.inserted_id is not None and result.acknowledged is True:
        logger.debug(msg=f'Database record insert SUCCESS! Location: {message.guild.id}/{message.channel.id}/{message.id}')
        pass
    else:
        logger.critical(msg=f'Database record insert failed! Incident Location: {message.guild.id}/{message.channel.id}/{message.id}')

async def attachmentCacher(attachment: discord.Attachment, message_id: int, filename: str):
    #drop attachments larger than 25M ~Snoopie
    if attachment.size > 25000000:
        logger.warning(msg=f'Attachment download dropped! Limit Exceeded. ' + f'Filename: {message_id}.{attachment.filename} ' + f'Size: {int(attachment.size / 1048576)}MB ' + f'Type: {attachment.content_type}')
        return
    cacheName = str(f'./AttachmentCache/{message_id}.{filename}')
    await attachment.save(fp=cacheName, use_cached=False)
    #Downloaded? I hope so, lets compress it. ~Snoopie
    logger.debug(msg=f'Attachment Downloaded! ' + f'Filename: {cacheName} ' + f'Size: {round(float(attachment.size / 1048576), 2)}MB ' + f'Type: {attachment.content_type}')
    if 'image' in attachment.content_type:
        image = Image.open(cacheName)
        image.save(cacheName, optimize=True, quality=10)

def database_insert_audit_log_entry(entry: discord.AuditLogEntry):
    result = log_database[str(entry.guild.id)].audit_log.insert_one(recursive_object_to_dict(entry))
    if result.inserted_id is not None and result.acknowledged is True:
        pass
    else:
        logger.warning(self=logger, msg=f'Audit log database record insert failed!')

def database_delete_message(message: discord.Message or classmethod): # Marks message as deleted in the message docs
    result = log_database[str(message.guild.id)][str(message.channel.id)].update_many({'message_id': str(message.id)}, {'$set': {'deleted': True}})
    if result is None:
        #this is bad, very bad, glad it's handled x3 ~Snoopie
        #Incident location is formatted like discord jump links, in fact you can copy and paste it after https://discord.com/channels/ and have a working jump link. ~Snoopie
        logger.critical(msg=f'Delete database record update failed! Fetched record empty. Incident Location: {message.guild.id}/{message.channel.id}/{message.id}')

async def database_get_last_message(bot: commands.Bot, guild_id: int, channel_id: int, message_id: int):
    message_doc = log_database[str(guild_id)][str(channel_id)].find_one({'message_id': str(message_id)}, sort=[('edited_at', DESCENDING)])
    if message_doc is None:
        message_doc = {}
        class message_author: #pylint: disable=invalid-name
            bot = False
    else:
        message_author = await bot.fetch_user(message_doc['author_id'])

    guild_object = bot.get_guild(guild_id)
    attachment0data = str(message_doc.get('attachment0', ''))
    class Message:
        id = message_id
        author = message_author
        guild = guild_object
        channel = guild.get_channel(channel_id)
        created_at = message_doc.get('created_at', None)
        edited_at = message_doc.get('edited_at', None)
        content = message_doc.get('content', '')
        type = discord.MessageType.default
        #this is really really bad, but better than my first idea of storing Base64 in the databse. ~Snoopie
        attachments = attachment0data.split("//FILENAME//", 1)

    return Message
