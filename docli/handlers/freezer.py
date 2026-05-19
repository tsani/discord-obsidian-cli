import re
import random

import aiofiles

from ..env import TASK_TAG
from ..formatting import RESPONSES
from ..io import git_transaction, git_pull, append_line
from . import ChannelHandler, DiscordArgumentParser

# Matches a freezer inventory line, capturing quantity (group 1) and the rest (group 2).
# e.g. "- 3 packs [[Chili]]" -> quantity="3", rest="packs [[Chili]]"
LINE_RE = re.compile(r'^- (\d+)\b(.*)$')


def _strip_wikilinks(s):
    return re.sub(r'\[\[(.+?)\]\]', r'\1', s)


async def _read_lines(path):
    async with aiofiles.open(path, 'r') as f:
        return (await f.read()).splitlines()


async def _write_lines(path, lines):
    async with aiofiles.open(path, 'w') as f:
        await f.write('\n'.join(lines) + '\n')


def _find_item_line(lines, item_name):
    """Find lines matching item_name (case-insensitive). Returns list of indices."""
    needle = item_name.lower()
    matches = []
    for i, line in enumerate(lines):
        if not line.startswith('- '):
            continue
        plain = _strip_wikilinks(line).lower()
        if needle in plain:
            matches.append(i)
    return matches


class FreezerHandler(ChannelHandler):
    def __init__(self, target_path, inventory_path):
        self.parser = DiscordArgumentParser(prog='freezer', add_help=True)
        self.parser.add_argument('command', choices=['plus', 'minus', 'exactly', 'list'])
        self.parser.add_argument('quantity', type=int, nargs='?')
        self.parser.add_argument('item', nargs='*', help='item name')
        self.target_path = target_path
        self.inventory_path = inventory_path

    async def _list(self, channel):
        await git_pull()
        lines = await _read_lines(self.inventory_path)
        items = [_strip_wikilinks(l) for l in lines if l.startswith('- ')]
        if not items:
            await channel.send('Freezer is empty!')
            return
        await channel.send('\n'.join(items))

    async def _fallback_todo(self, channel, args, item, reason):
        """Add a manual-processing todo when we can't auto-update the inventory."""
        entry = f'{args.command} {args.quantity} [[{item}]]'
        content = f'- [ ] {TASK_TAG}#freezer {entry}'
        async with git_transaction(f'freezer: {entry}') as g:
            await append_line(self.target_path, content)
            g.add(self.target_path)
        await channel.send(f'{reason} Added a todo instead.')

    async def _update_inventory(self, channel, args):
        item = ' '.join(args.item)
        if args.quantity is None:
            await channel.send('Usage: `plus|minus|exactly <quantity> <item>`')
            return

        async with git_transaction(f'freezer: {args.command} {args.quantity} {item}') as g:
            lines = await _read_lines(self.inventory_path)
            matches = _find_item_line(lines, item)

            if len(matches) == 0:
                await append_line(self.target_path,
                    f'- [ ] {TASK_TAG}#freezer {args.command} {args.quantity} [[{item}]]')
                g.add(self.target_path)
                await channel.send(f'Item not found in inventory. Added a todo instead.')
                return

            if len(matches) > 1:
                await append_line(self.target_path,
                    f'- [ ] {TASK_TAG}#freezer {args.command} {args.quantity} [[{item}]]')
                g.add(self.target_path)
                await channel.send(f'Multiple matches found. Added a todo instead.')
                return

            idx = matches[0]
            line = lines[idx]
            m = LINE_RE.match(line)
            if not m:
                await append_line(self.target_path,
                    f'- [ ] {TASK_TAG}#freezer {args.command} {args.quantity} [[{item}]]')
                g.add(self.target_path)
                await channel.send(f"Couldn't parse the inventory line. Added a todo instead.")
                return

            old_qty = int(m.group(1))
            rest = m.group(2)

            if args.command == 'plus':
                new_qty = old_qty + args.quantity
            elif args.command == 'minus':
                new_qty = old_qty - args.quantity
            else:  # exactly
                new_qty = args.quantity

            if new_qty <= 0:
                lines.pop(idx)
            else:
                lines[idx] = f'- {new_qty}{rest}'

            await _write_lines(self.inventory_path, lines)
            g.add(self.inventory_path)

            if new_qty <= 0:
                await channel.send(f'Removed {_strip_wikilinks(line.removeprefix("- ").strip())} from the freezer.')
            else:
                await channel.send(f'Updated: {_strip_wikilinks(lines[idx])}')

    async def cmd(self, channel, args):
        if args.command == 'list':
            return await self._list(channel)
        await self._update_inventory(channel, args)
