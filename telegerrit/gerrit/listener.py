import logging
import sys

from pygerrit.client import GerritClient
from pygerrit.events import CommentAddedEvent

from telegerrit.gerrit.models import UserMap, CommentsWriter
from telegerrit.settings import ssh_config, gerrit_url_template
from telegerrit.telegram.bot import send_message


logger = logging.getLogger(__name__)


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
        # send message if subscribed
        if (event.author.name == u'Jenkins' and
                event.comment == u'Patch Set 1: Verified+1'):
            return

        for chat_id in UserMap.get_user_ids():
            if CommentsWriter.is_notified(chat_id=chat_id):
                msg = u';\n'.join([
                    event.comment,
                    event.change.owner.name+unicode(event.change),
                    gerrit_url_template.format(change_id=event.change.number),
                    event.author.name
                ])
                logger.info(msg)
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
    sys.exit(main(ssh_config))
