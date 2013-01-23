"""Platformer Node.

Usage:
  platformer.py [--port=<port>] [--name=<name>] [--reinit-db]

Options:
  --port=<port>   Port to use [default: 5000]
  --name=<name>   Name to assign to this node [default: local]
  --reinit-db     Reinitialize (empty) the database

"""
from datetime import datetime

from docopt import docopt

import flask
import flask.ext.restless
import flask.ext.sqlalchemy

import requests

from database import db
from models import (
    Memo,
    Peer,
    ReliabilityMetadata,
)


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

        # Note that route definitions have to go here, because the app is not global.
        @self.app.route('/', methods=['HEAD'])
        def pong():
            return ''


    def check_peer(self, url):
        url = unicode(url) if not isinstance(url, unicode) else url
        with self.app.app_context():
            peer = db.session.query(Peer).filter(Peer.url == url).first()

            if not peer:
                peer = Peer(url=url,
                            active=False,
                            health=0.0,
                            )

            r = requests.head(url)
            peer.active = r.status_code == 200
            peer.health = (peer.health + (1.0 if peer.active else 0.0)) / 2.0
            peer.last_checked = datetime.utcnow()

            db.session.add(peer)
            db.session.commit()

            return peer.active


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Platformer Node 0.1')
    node = Node(arguments['--name'], reinit_db=arguments['--reinit-db'])
    node.app.run(debug=True, port=int(arguments['--port']))
