import random
from datetime import date

from ..env import TASK_TAG
from ..formatting import EMOJI, RESPONSES
from ..io import git_transaction, append_line
from . import ChannelHandler, DiscordArgumentParser

class GroceryHandler(ChannelHandler):
    def __init__(self, target_path):
        self.parser = DiscordArgumentParser(prog='grocery', add_help=True)
        self.parser.add_argument('item', nargs='+', help='item name')
        self.target_path = target_path

    async def cmd(self, channel, args):
        if len(args.item) == 1:
            if args.item[0] == 'list':
                return await self._grocery_list(channel)
            else:
                item = f'[[{args.item[0]}]]'
        else:
            item = ' '.join(args.item)
        content = f'- [ ] {TASK_TAG}#grocery {item}'
        async with git_transaction(f'grocery: {item}') as g:
            await append_line(self.target_path, content)
            g.add(self.target_path)
        await channel.send(random.choice(RESPONSES))
