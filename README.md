# discord-obsidian-cli

A Discord bot that acts as a command-line interface into an [Obsidian](https://obsidian.md/) vault. Each Discord channel is mapped to a handler; when you send a message in that channel the bot parses it as a command, appends a formatted Markdown line to a file in the vault, and commits and pushes the change via git.

## How it works

1. The bot listens for messages on every channel it can see.
2. It looks up the channel name in `CHANNEL_HANDLERS` (defined in `docli/config.py`).
3. If a handler is registered for that channel, the message content is parsed as arguments and the handler runs.
4. Every write goes through a **git transaction**: `pull --rebase` → write → `add` → `commit` → `push`. The vault is a plain git repository that Obsidian syncs from.

## Handlers

### `todo` — append a to-do item

Channel name: **todo**

```
buy more coffee
```

Appends to `TODO_PATH`:

```
- [ ] #task buy more coffee
```

### `track` — log a completed habit

Channel name: **track**

```
morning run
```

Appends to `HABITS_PATH`:

```
- [x] #task #habit/morning-run 📅 2025-01-15 ✅ 2025-01-15
```

### `grocery` — manage a grocery list

Channel name: **grocery**

Add one or more items (comma-separated):

```
milk, eggs, bread
```

Appends to `GROCERY_PATH`:

```
- [ ] #task #grocery [[milk]]
- [ ] #task #grocery [[eggs]]
- [ ] #task #grocery [[bread]]
```

List current items (searches the entire vault for unchecked grocery tasks):

```
list
```

### `freezer` — track freezer inventory changes

Channel name: **freezer**

```
plus 2 whole chicken
minus 1 pizza
exactly 3 broccoli
```

Appends to `FREEZER_PATH`:

```
- [ ] #task #freezer plus 2 [[whole chicken]]
```

The first word must be `plus`, `minus`, or `exactly`. The second must be an integer. Everything after is the item name, wrapped in Obsidian wikilinks.

## Deployment

The bot ships as a Docker image. On startup the entrypoint clones `GIT_UPSTREAM` into `/vault` (if not already present), configures git identity, and launches the bot.

### 1. Create `.env`

```dotenv
BOT_TOKEN=your-discord-bot-token
GIT_EMAIL=bot@example.com
GIT_UPSTREAM=git@github.com:you/your-vault.git
```

`.env` is gitignored and never baked into the image.

### 2. Provide an SSH key

The container mounts your SSH private key read-only so it can push to the vault repository:

```yaml
volumes:
  - $HOME/.ssh/id_rsa:/root/.ssh/id_rsa:ro
```

The key must have write access to `GIT_UPSTREAM`. `StrictHostKeyChecking` is set to `accept-new` on first run.

### 3. Configure environment variables

All path values are **relative to the vault root** (`/vault`).

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | yes | Discord bot token (put in `.env`) |
| `VAULT_DIR` | yes | Absolute path to vault inside container — set to `/vault` |
| `GIT_UPSTREAM` | yes | SSH URL of the vault git remote (put in `.env`) |
| `GIT_EMAIL` | yes | Git commit author email (put in `.env` or compose file) |
| `GIT_NAME` | yes | Git commit author name |
| `TASK_TAG` | no | Prefix inserted before every task tag, e.g. `#task` |
| `TODO_PATH` | if using `todo` handler | Vault-relative path, e.g. `Todo.md` |
| `HABITS_PATH` | if using `track` handler | Vault-relative path, e.g. `Habits.md` |
| `GROCERY_PATH` | if using `grocery` handler | Vault-relative path, e.g. `Grocery.md` |
| `FREEZER_PATH` | if using `freezer` handler | Vault-relative path, e.g. `Freezer.md` |

### 4. Configure handlers

`docli/config.py` maps Discord channel names to handler instances. The default config only wires up `todo` and `track`:

```python
# docli/config.py (default)
from .handlers.track import TrackHandler
from .handlers.todo import TodoHandler
from os import environ

CHANNEL_HANDLERS = {
    'track': TrackHandler(environ['HABITS_PATH']),
    'todo':  TodoHandler(environ['TODO_PATH']),
}
```

To add the `grocery` and `freezer` handlers, create a local `config.py` and **mount it over the one inside the image**:

```python
# config.py (local override)
from docli.handlers.track import TrackHandler
from docli.handlers.todo import TodoHandler
from docli.handlers.grocery import GroceryHandler
from docli.handlers.freezer import FreezerHandler
from os import environ

CHANNEL_HANDLERS = {
    'track':   TrackHandler(environ['HABITS_PATH']),
    'todo':    TodoHandler(environ['TODO_PATH']),
    'grocery': GroceryHandler(environ['GROCERY_PATH']),
    'freezer': FreezerHandler(environ['FREEZER_PATH']),
}
```

Then in `docker-compose.yml`, uncomment the config volume mount and add the extra env vars:

```yaml
services:
  docli:
    image: jerrington/docli:latest
    env_file: .env
    environment:
      - "VAULT_DIR=/vault"
      - "TODO_PATH=Todo.md"
      - "HABITS_PATH=Habits.md"
      - "GROCERY_PATH=Grocery.md"
      - "FREEZER_PATH=Freezer.md"
      - "TASK_TAG=#task"
      - "GIT_NAME=Discord Obsidian CLI"
    volumes:
      - vault:/vault
      - $HOME/.ssh/id_rsa:/root/.ssh/id_rsa:ro
      - ./config.py:/app/docli/config.py   # <-- mount your custom config

volumes:
  vault:
```

### 5. Build and run

```bash
# Build the image locally
./build

# Start the bot
docker-compose up -d
```

## Discord bot setup

1. Create an application at <https://discord.com/developers/applications>.
2. Under **Bot**, enable the **Message Content** privileged intent.
3. Generate an invite URL with the `bot` scope and at minimum the **Send Messages** and **Read Message History** permissions.
4. Invite the bot to your server and create channels whose names match the handlers you have configured.
