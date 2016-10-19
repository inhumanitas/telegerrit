import logging
import sys
from time import sleep

from pygerrit.client import GerritClient
from pygerrit.error import GerritError
from pygerrit.events import CommentAddedEvent, PatchsetCreatedEvent

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
        not_connected = True
        while not_connected:
            try:
                self.client.gerrit_version()
                not_connected = False
            except GerritError as e:
                logger.error(e)
                sleep(3)

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
                u'Verified+1' in event.comment):
            return

        for chat_id, username in UserMap.get_users():
            if event.author.username == username:
                continue

            # TODO All various notification rules should be refactored
            if CommentsWriter.is_notified(chat_id=chat_id):
                msg = u';\n'.join([
                    event.comment + u' by ' + event.author.name,
                    event.change.owner.name+unicode(event.change),
                    event.change.subject,
                    gerrit_url_template.format(change_id=event.change.number),
                ])
                logger.info(msg)
                send_message(chat_id, msg)


class PatchsetCreatedEventEventHandler(CommentAddedEventHandler):
    @classmethod
    def run(cls, event):
        # send message if subscribed
        for chat_id in UserMap.get_users():
            if CommentsWriter.is_notified(chat_id=chat_id):
                msg = u';\n'.join([
                    event.name + u' by ' + event.uploader.name,
                    event.change.owner.name+unicode(event.change),
                    gerrit_url_template.format(change_id=event.change.number),
                ])
                logger.info(msg)
                send_message(chat_id, msg)


events = {
    CommentAddedEvent: CommentAddedEventHandler,
    PatchsetCreatedEvent: PatchsetCreatedEventEventHandler,
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
