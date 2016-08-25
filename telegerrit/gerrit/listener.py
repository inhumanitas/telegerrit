# from gerrit import filters
# from gerrit import reviews
#
# # gerrit_host = 'http://10.10.31.147/'
# gerrit_host = '10.10.31.147'
#
# project = filters.OrFilter()
# # project.add_items('project', ['tionix-client', 'tionix-dash'])
#
# change = filters.AndFilter()
# change.add_items('change', [2389])
#
# comment = filters.AndFilter()
# comment.add_items('comment', [1])
#
#
# other = filters.Items()
# other.add_items('is', 'open')
# other.add_items('limit', 100)
#
# query = reviews.Query(host=gerrit_host, user='d.valiullin',
#                       # key='C:\ssh-key\id_rsa.pub')
#                       key='C:\Users\user\.ssh\id_rsa.pub')
# for review in query.filter(comment, other):
# # for review in query.filter(project, other):
#     print review
from pygerrit.client import GerritClient
from pygerrit.events import CommentAddedEvent


class GerritClientEventStream(GerritClient):

    def __init__(self, host, username=None, port=None, keepalive=None):
        super(GerritClientEventStream, self).__init__(host, username, port,
                                                      keepalive)

        self.client = GerritClient(host, username, port, keepalive)

    def __str__(self):
        return

    def __enter__(self):
        self.client.start_event_stream()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.stop_event_stream()


def main(*args, **kwars):
    with GerritClientEventStream(*args, **kwars) as client:
        while True:
            print client.get_event()


class EventHandler(object):
    def run(self, event):
        raise NotImplemented()


class CommentAddedEventHandler(EventHandler):
    def run(self, event):
        pass

events = {
    CommentAddedEvent: CommentAddedEventHandler,
}


if __name__ == '__main__':
    # main('review')
    cli = GerritClient('review')
    cli.start_event_stream()
    while True:
        event = cli.get_event()
        event_handler = events.get(event.__class__)
        if event_handler:
            assert issubclass(event_handler.__class__, EventHandler)
            event_handler(event)

    cli.stop_event_stream()
