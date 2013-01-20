"""Platformer Node.

Usage:
  node.py [--port=<port>]

Options:
  --port=<port>   Port to use [default: 5000]

"""
from docopt import docopt
from flask import Flask


app = Flask('platformer_node')

@app.route('/', methods=['HEAD'])
def pong():
    return ''


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Platformer Node 0.1')
    app.run(debug=True,
            port=int(arguments['--port']))
