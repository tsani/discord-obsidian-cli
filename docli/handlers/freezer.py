import random
from datetime import date

from ..env import TASK_TAG
from ..formatting import EMOJI, RESPONSES
from ..io import git_transaction, append_line
from . import ChannelHandler, DiscordArgumentParser

class FreezerHandler(ChannelHandler):
    def __init__(self, target_path):
        self.parser = DiscordArgumentParser(prog='freezer', add_help=True)
        self.parser.add_argument('command', choices=['plus', 'minus', 'exactly'])
        self.parser.add_argument('quantity', type=int)
        self.parser.add_argument('item', nargs='+', help='item name')
        self.target_path = target_path

    async def cmd(self, channel, args):
        item = ' '.join(args.item)
        entry = f'{args.command} {args.quantity} [[{item}]]'
        content = f'- [ ] {TASK_TAG}#freezer {entry}'
        async with git_transaction(f'freezer: {entry}') as g:
            await append_line(self.target_path, content)
            g.add(self.target_path)
        await channel.send(random.choice(RESPONSES))
