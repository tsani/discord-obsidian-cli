import random
from datetime import date

from ..formatting import EMOJI, RESPONSES
from ..io import git_transaction, append_line
from . import ChannelHandler, DiscordArgumentParser

class TrackHandler(ChannelHandler):
    def __init__(self, target_path):
        self.parser = DiscordArgumentParser(prog='track', add_help=True)
        self.parser.add_argument('habit', nargs='+', help='habit name')
        self.target_path = target_path

    async def cmd(self, channel, args):
        t = date.today().strftime("%Y-%m-%d")
        habit = ' '.join(args.habit).lower().replace(' ', '-')
        habit_content = f'- [x] {TASK_TAG}#habit/{habit} {EMOJI["calendar"]} {t} {EMOJI["checkmark"]} {t}'
        async with git_transaction(f'habit: {habit} {t}') as g:
            await append_line(self.target_path, habit_content)
            g.add(self.target_path)
        await channel.send(random.choice(RESPONSES))
