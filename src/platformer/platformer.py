"""Platformer Node.

Usage:
  platformer.py [--port=<port>] [--name=<name>] [--reinit-db]

Options:
  --port=<port>   Port to use [default: 5000]
  --name=<name>   Name to assign to this node [default: local]
  --reinit-db     Reinitialize (empty) the database

"""
from docopt import docopt
import flask
import flask.ext.restless
import flask.ext.sqlalchemy

from database import db
from models import (
    Memo,
    Peer,
    ReliabilityMetadata,
)


app = flask.Flask(__name__)

def setup_app(reinit_db=False):
    db.init_app(app)
    with app.app_context():
        if reinit_db:
            db.drop_all()
        db.create_all()
    manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
    manager.create_api(Peer, url_prefix='',
                       methods=['GET', 'POST', 'PUT', 'DELETE'],
                       include_columns=['url'])


@app.route('/', methods=['HEAD'])
def pong():
    return ''


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Platformer Node 0.1')
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'sqlite:///platformer_node_{}.db'.format(arguments['--name'])
    setup_app(reinit_db=arguments['--reinit-db'])

    app.run(debug=True,
            port=int(arguments['--port']))
