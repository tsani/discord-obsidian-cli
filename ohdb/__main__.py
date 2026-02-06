import asyncio
import discord
import random
from urllib.parse import quote
from os import getenv
import sys

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

BOT_TOKEN = getenv('BOT_TOKEN') or die('missing BOT_TOKEN env var')
VAULT_DIR = getenv('VAULT_DIR') or die('missing VAULT_DIR env var')

RESPONSES = [
    'OK boss 👍',
    'Yass queen 💅',
    'Sir yes sir 🫡',
]

async def add_todo(message):
    todo_string = quote(f'- [ ] #task {message.content.lower()}')
    proc = await asyncio.create_subprocess_exec(
        '/usr/bin/xdg-open',
        f"obsidian://new?silent&vault=household-vault&append&file=meta%2fTask%20list&content={todo_string}",
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    await message.channel.send(random.choice(RESPONSES))
    print('added a todo')

async def handle_cli(message):
    if message.content == 'groceries':
        proc = await asyncio.create_subprocess_shell(
            f'find {VAULT_DIR} -name "*.md" -exec grep -e "^- \\[ \\]" {{}} \\; '
            '| grep "#task" | grep -i "#grocery"',
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(None)
        await message.channel.send(stdout.decode().strip())
    else:
        await message.channel.send('unknown command')

class OHDB(discord.Client):
    async def on_ready(self):
        print('ready!')

    async def on_message(self, message):
        if message.author == self.user: return

        if message.channel.name == 'todo-obsidian':
            return await add_todo(message)
        if message.channel.name == 'the-terminal':
            return await handle_cli(message)

intents = discord.Intents.default()
intents.message_content = True

client = OHDB(intents=intents)
client.run(BOT_TOKEN)
