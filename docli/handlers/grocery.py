import re
import random
import subprocess
from datetime import date

from ..env import TASK_TAG, VAULT_DIR
from ..formatting import EMOJI, RESPONSES
from ..io import git_transaction, append_line
from . import ChannelHandler, DiscordArgumentParser

class GroceryHandler(ChannelHandler):
    def __init__(self, target_path):
        self.parser = DiscordArgumentParser(prog='grocery', add_help=True)
        self.parser.add_argument('item', nargs='+', help='item name')
        self.target_path = target_path

    async def _grocery_list(self, channel):
        prefix = f'- [ ] {TASK_TAG}#grocery'
        prefix_re = f'- \\[ \\] {TASK_TAG}#grocery' # yuck
        result = subprocess.run(
            ['find', VAULT_DIR, '-name', '*.md', '-exec', 'grep', '-h', '--', prefix_re, '{}', '+'],
            capture_output=True, text=True,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        if not lines:
            await channel.send('Grocery list is empty!')
            return
        items = []
        for line in lines:
            item = line.removeprefix(prefix).strip()
            item = re.sub(r'\[\[(.+?)\]\]', r'\1', item)
            items.append(item)
        await channel.send('\n'.join(f'- {item}' for item in items))

    async def cmd(self, channel, args):
        if len(args.item) == 1 and args.item[0] == 'list':
            return await self._grocery_list(channel)

        item = ' '.join(args.item)
        items = item.split(', ')
        async with git_transaction(f'grocery: {item}') as g:
            for item in items:
                content = f'- [ ] {TASK_TAG}#grocery [[{item}]]'
                await append_line(self.target_path, content)
            g.add(self.target_path)
        await channel.send(random.choice(RESPONSES))
