import logging
import os
import sys
from os import getenv

log = logging.getLogger(__name__)

def die(msg):
    log.critical(msg)
    sys.exit(1)

BOT_TOKEN = getenv('BOT_TOKEN') or die('missing BOT_TOKEN env var')
VAULT_DIR = getenv('VAULT_DIR') or die('missing VAULT_DIR env var')

TASK_TAG = getenv('TASK_TAG') or ''
if TASK_TAG: TASK_TAG += ' '
