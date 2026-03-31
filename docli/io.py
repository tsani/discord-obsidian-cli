import asyncio
import aiofiles
from contextlib import asynccontextmanager

from .exceptions import Error
from .env import VAULT_DIR

async def git(vault_dir, *args):
    proc = await asyncio.create_subprocess_exec(
        'git', '-C', vault_dir, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Error(f'git {args[0]} failed: {stderr.decode().strip()}')


async def append_line(path, line):
    async with aiofiles.open(path, 'a+') as f:
        await f.seek(0, 2)
        pos = await f.tell()
        if pos > 0:
            await f.seek(pos - 1)
            if await f.read(1) != '\n':
                await f.write('\n')
        await f.write(line + '\n')

@asynccontextmanager
async def git_transaction(message):
    await git(VAULT_DIR, 'pull', '--rebase')
    paths = []
    class G:
        def add(self, path):
            paths.append(path)
    yield G()
    for path in paths:
        await git(VAULT_DIR, 'add', path)
    await git(VAULT_DIR, 'commit', '-m', message)
    await git(VAULT_DIR, 'push')

