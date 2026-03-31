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

TODO_PATH = getenv('TODO_PATH')
TODO_PATH = os.path.join(VAULT_DIR, TODO_PATH) \
    if TODO_PATH else os.path.join(VAULT_DIR, 'Todo.md')

HABITS_PATH = getenv('HABITS_PATH') or os.path.join(VAULT_DIR, 'Habits.md')
HABITS_PATH = os.path.join(VAULT_DIR, HABITS_PATH) \
    if HABITS_PATH else os.path.join(VAULT_DIR, 'Habits.md')

TASK_TAG = getenv('TASK_TAG') or ''
if TASK_TAG: TASK_TAG += ' '
