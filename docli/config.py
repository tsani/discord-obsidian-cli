from .handlers.track import TrackHandler
from .handlers.todo import TodoHandler

from os import environ

CHANNEL_HANDLERS = {
    'track': TrackHandler(environ['HABITS_PATH]'),
    'todo': TodoHandler(environ['TODO_PATH']),
}
