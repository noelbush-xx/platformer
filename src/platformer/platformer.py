"""Platformer Node.

Usage:
  platformer.py [--port=<port>] [--name=<name>] [--reinit-db]

Options:
  --port=<port>   Port to use [default: 5000]
  --name=<name>   Name to assign to this node [default: local]
  --reinit-db     Reinitialize (empty) the database

"""
from datetime import datetime
import json
import random
import string

from docopt import docopt

import flask
import flask.ext.restless
from collections import namedtuple

import flask.ext.sqlalchemy

import requests

from database import db
from models import (
    Memo,
    Peer,
    ReliabilityMetadata,
    Secret,
)


PeerStatusCheck = namedtuple('PeerStatus', ['active', 'last_checked'])


class Node(object):

    def __init__(self, name, config=None, reinit_db=False):
        if not config:
            config = {'SQLALCHEMY_DATABASE_URI':
                      'sqlite:///platformer_node_{}.db'.format(name)}
        self.app = flask.Flask(__name__)
        self.app.config.update(config)
        db.init_app(self.app)
        with self.app.app_context():
            if reinit_db:
                db.drop_all()
            db.create_all()

        manager = flask.ext.restless.APIManager(self.app, flask_sqlalchemy_db=db)
        manager.create_api(Peer, url_prefix='',
                           methods=['GET', 'POST', 'PUT', 'DELETE'],
                           include_columns=['url'])
        manager.create_api(Secret, url_prefix='', methods=['POST'])

        # Note that route definitions have to go here, because the app is not global.
        @self.app.route('/', methods=['HEAD'])
        def pong():
            return ''


    RANDOM_CHARS = string.ascii_letters + string.digits

    def is_me(self, url):
        """
        Determining whether a peer is actually this node is tricky.  We cannot
        just compare hostnames and ports, since a node may run on different
        ports, use different hostnames (or IP addresses), or even not be running
        a web app at all.

        If we do have HTTP access to another node, the best thing we can do is
        post a secret value to that node, then check in our own database to see
        if we have the same secret value.  If we do, we know we're talking to
        (about) ourselves.
        """
        secret = u''.join(random.choice(self.RANDOM_CHARS) for x in range(255))
        response = requests.post('{}/secret'.format(url),
                          data=json.dumps({'secret': secret}))

        if response.status_code != 201:
            raise PeerUnreachable(url)

        with self.app.app_context():
            found = db.session.query(Secret).filter(Secret.secret == secret).first()

            return bool(found)


    def get_or_create_peer_record(self, url):
        with self.app.app_context():
            peer = db.session.query(Peer).filter(Peer.url == url).first()
            if not peer:
                peer = Peer(url=url,
                            active=False,
                            health=0.0,
                            )
        return peer


    def add_peer(self, url):
        """
        Add a record about a peer that exists at the given URL.  Don't add the
        record if the peer is actually me (raise an exception then).  If I
        already have a record about the peer, it will be updated.  Return
        updated status information about the peer.
        """
        if self.is_me(url):
            raise PeerIsMe

        # Ensure URL is unicode.
        url = unicode(url) if not isinstance(url, unicode) else url

        peer = self.get_or_create_peer_record(url)

        status = self.check_peer(url)
        self.update_status(peer, status)
        return status


    def update_status(self, peer, status):
        """
        Update my record of the given peer using the information in status.
        """
        with self.app.app_context():
            peer.active = status.active
            peer.health = (peer.health + (1.0 if status.active else 0.0)) / 2.0
            peer.last_checked = status.last_checked

            db.session.add(peer)
            db.session.commit()


    def check_peer(self, url):
        """
        Check on the peer at the given URL and return status information.
        """
        response = requests.head(url)
        return PeerStatusCheck(active=response.status_code == 200,
                               last_checked=datetime.utcnow())


    def get_peer_list_from(self, url):
        """
        Ask a peer at the given URL for its peer list.  Add each one from
        the list.
        """
        response = requests.get('{}/peer'.format(url))
        get_response = json.loads(response.content)
        for obj in get_response['objects']:
            try:
                self.add_peer(obj['url'])
            except PeerIsMe:
                # No problem in this case.
                pass


class PeerIsMe(Exception):
    """
    To be thrown when a node is asked to communicate with or store information
    about a peer which is in fact itself.
    """
    pass


class PeerUnreachable(Exception):

    def __init__(self, url):
        self.url = url


    def __str__(self):
        return 'Could not reach peer at {}.'.format(self.url)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Platformer Node 0.1')
    node = Node(arguments['--name'], reinit_db=arguments['--reinit-db'])
    node.app.run(debug=True, port=int(arguments['--port']))
