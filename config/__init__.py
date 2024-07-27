import logging
import os

logger = logging.getLogger(name='WGEDLA')

#I mean, running it without those files is possible now ~Snoopie
if os.path.exists('config/settings.py') is False:
    logger.critical(msg='config/settings.py is missing! Please configure and, RE-NAME settings_example.py')
    exit(1)
if os.path.exists('config/secrets.py') is False:
    logger.critical(msg='config/secrets.py is missing! Please configure and, RE-NAME secrets_example.py')
    exit(2)

from . import secrets
from . import settings