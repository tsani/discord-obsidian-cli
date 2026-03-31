from .handlers.track import TrackHandler
from .handlers.todo import TodoHandler

from . import env

CHANNEL_HANDLERS = {
    'track': TrackHandler(env.HABITS_PATH),
    'todo': TodoHandler(env.TODO_PATH),
}
