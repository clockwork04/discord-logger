#WGEDLA v0.9 Example Configuration File
#To setup, please adjust values to your liking, then rename to settings.py before running.

#Command prefix for built-in commands
COMMAND_PREFIX = '~'

#Channel ID for bot status messages
DEV_CHANNEL = 000000000000000000

#Discord Application ID (https://discord.com/developers/applications)
APPLICATION_ID = 'REPLACE00000000000'

#"Super User" IDs for built-in commands
DEVELOPER_IDS = ["REPLACE00000000000"]

#Bot user invisibility
INVISIBLE_STATUS = False

#Bot user statuses
CUSTOM_STATUS = ["Sometimes Watching x3", "Sometimes Peeking >:3c"]

#Bot status string rotation time (in seconds)
CUSTOM_STATUS_DELAY = 120

#User IDs of users whos actions are not to be logged (e.g. Message Proxy Bots, Moderators dealing with PII)
OPERATOR_WHITELIST_IDS = ["REPLACE00000000000", "REPLACE00000000001"]

#User IDs of users whom are not to be logged 
USER_WHITELIST_IDS = ["REPLACE00000000000", "REPLACE00000000001"]

#Time between posting and deletion where the message is not logged as deleted in milliseconds (e.g. Message Proxy Bots)
DELETE_COOLDOWN = 250

#Disables action whielisting, without affecting the whitelist
NSA_MODE = False