import asyncio
import logging
import os
import discord
import random
import argparse
import shlex
import aiofiles
from datetime import date
from os import getenv
import sys

logging.basicConfig(level=logging.INFO)
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

CHANNEL_NAME = getenv('CHANNEL_NAME') or die('missing CHANNEL_NAME env var')

RESPONSES = [
    'OK boss 👍',
    'Yass queen 💅',
    'Sir yes sir 🫡',
]

EMOJI = {
    'calendar': '📅',
    'checkmark': '✅',
}


async def git(vault_dir, *args):
    proc = await asyncio.create_subprocess_exec(
        'git', '-C', vault_dir, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Error(f'git {args[0]} failed: {stderr.decode().strip()}')


async def cmd_todo(channel, args):
    task = ' '.join(args.task).lower()
    todo_string = f'- [ ] {TASK_TAG}{task}'
    await git(VAULT_DIR, 'pull', '--rebase')
    async with aiofiles.open(TODO_PATH, 'a') as f:
        await f.write(todo_string + '\n')
    await git(VAULT_DIR, 'add', TODO_PATH)
    await git(VAULT_DIR, 'commit', '-m', f'todo: {task}')
    await git(VAULT_DIR, 'push')
    await channel.send(random.choice(RESPONSES))

async def cmd_track(channel, args):
    t = date.today().strftime("%Y-%m-%d")
    habit = ' '.join(args.habit).lower().replace(' ', '-')
    habit_content = f'- [x] {TASK_TAG}#habit/{habit} {EMOJI["calendar"]} {t} {EMOJI["checkmark"]} {t}'
    await git(VAULT_DIR, 'pull', '--rebase')
    async with aiofiles.open(HABITS_PATH, 'a') as f:
        await f.write(habit_content + '\n')
    await git(VAULT_DIR, 'add', HABITS_PATH)
    await git(VAULT_DIR, 'commit', '-m', f'habit: {habit} {t}')
    await git(VAULT_DIR, 'push')
    await channel.send(random.choice(RESPONSES))

COMMANDS = {
    'track': cmd_track,
    'todo': cmd_todo,
}

class Error(RuntimeError): pass

class DiscordArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises instead of calling sys.exit on error."""
    def error(self, message):
        raise Error(message)

    def exit(self, status=0, message=None):
        raise Error(message or '')

cli_parser = DiscordArgumentParser(prog='', add_help=True)
subparsers = cli_parser.add_subparsers(dest='command')

track_parser = subparsers.add_parser('track', help='track a habit for today')
track_parser.add_argument('habit', nargs='+', help='habit name')

todo_parser = subparsers.add_parser('todo', help='add a todo task')
todo_parser.add_argument('task', nargs='+', help='task description')

async def handle_cli(channel, message):
    try:
        args = cli_parser.parse_args(shlex.split(message))
    except Error as e:
        await channel.send(f'error: {e}')
        return
    if args.command is None:
        await channel.send(cli_parser.format_help())
        return
    handler = COMMANDS.get(args.command)
    if handler is None:
        await channel.send(f'error: unknown command {args.command}')
        return
    await handler(channel, args)

class DiscordObsidianCLI(discord.Client):
    async def on_ready(self):
        log.info('ready!')

    async def on_message(self, message):
        if message.author == self.user: return

        if message.channel.name == CHANNEL_NAME:
            async with message.channel.typing():
                try:
                    await handle_cli(message.channel, message.content)
                except Exception as e:
                    await message.channel.send(f'error: {e}')

intents = discord.Intents.default()
intents.message_content = True

client = DiscordObsidianCLI(intents=intents)
client.run(BOT_TOKEN)
