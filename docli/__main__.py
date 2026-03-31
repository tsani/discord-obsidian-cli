import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

import discord

from .config import CHANNEL_HANDLERS
from .env import BOT_TOKEN
from .exceptions import Error

class DiscordObsidianCLI(discord.Client):
    async def on_ready(self):
        log.info('ready!')

    async def on_message(self, message):
        if message.author == self.user: return
        handler = CHANNEL_HANDLERS.get(message.channel.name)
        if handler is None: return
        async with message.channel.typing():
            try:
                await handler.handle(message.channel, message.content)
            except Error as e:
                await message.channel.send(f'error: {e}')
            except Exception as e:
                await message.channel.send(f'error: {e}')

intents = discord.Intents.default()
intents.message_content = True

client = DiscordObsidianCLI(intents=intents)
client.run(BOT_TOKEN)
