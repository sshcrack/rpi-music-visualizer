from socketserver import ThreadingMixIn
from http.server import HTTPServer


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ This class allows to handle requests in separated threads.
        No further content needed, don't touch this. """
