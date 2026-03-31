import shlex
import argparse
from ..exceptions import Error

class DiscordArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises instead of calling sys.exit on error."""
    def error(self, message):
        raise Error(message)

    def exit(self, status=0, message=None):
        raise Error(message or '')

class ChannelHandler:
    async def handle(self, channel, message):
        args = self.parser.parse_args(shlex.split(message))
        await self.cmd(channel, args)

    async def cmd(self, channel, args):
        raise NotImplementedError
