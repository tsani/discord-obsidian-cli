import random

from ..env import TASK_TAG
from ..formatting import RESPONSES
from ..io import git_transaction, append_line
from . import ChannelHandler, DiscordArgumentParser

class TodoHandler(ChannelHandler):
    def __init__(self, target_path):
        self.parser = DiscordArgumentParser(prog='todo', add_help=True)
        self.parser.add_argument('task', nargs='+', help='task description')
        self.target_path = target_path

    async def cmd(self, channel, args):
        task = ' '.join(args.task).lower()
        async with git_transaction(f'todo: {task}') as g:
            await append_line(self.target_path, f'- [ ] {TASK_TAG}{task}')
            g.add(self.target_path)
        await channel.send(random.choice(RESPONSES))
