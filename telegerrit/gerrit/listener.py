
import sys
from pygerrit.client import GerritClient
from pygerrit.events import CommentAddedEvent

from telegerrit.gerrit.models import UserMap, CommentsWriter
from telegerrit.telegram.bot import send_message


class GerritClientEventStream(GerritClient):

    def __init__(self, host, username=None, port=None, keepalive=None):
        super(GerritClientEventStream, self).__init__(host, username, port,
                                                      keepalive)

        self.client = GerritClient(host, username, port, keepalive)

    def __str__(self):
        return

    def __enter__(self):
        # Needed to make event stream to be connected to server
        self.client.gerrit_version()
        self.client.start_event_stream()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.stop_event_stream()


class EventHandler(object):
    @classmethod
    def run(cls, event):
        raise NotImplemented()


class CommentAddedEventHandler(EventHandler):
    @classmethod
    def run(cls, event):
        # take telegram user by gerrit username event.author.username
        chat_id = UserMap.get_by_gerrit_username(event.author.username)
        # send message if subscribed
        if chat_id and CommentsWriter.get(chat_id):
            msg = u'; '.join([unicode(event.change),
                              event.author.name,
                              event.comment])
            send_message(chat_id, msg)


events = {
    CommentAddedEvent: CommentAddedEventHandler,
}


def main(*args, **kwars):
    with GerritClientEventStream(*args, **kwars) as client:
        while True:
            event = client.get_event()
            event_handler = events.get(event.__class__)
            if event_handler:
                assert issubclass(event_handler, EventHandler)
                event_handler.run(event)


if __name__ == '__main__':
    sys.exit(main('review'))
