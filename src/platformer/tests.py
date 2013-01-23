import json
import os
from os.path import abspath, dirname, join
import subprocess
import sys
import tempfile
from time import sleep
import unittest

from platformer import Node


class TestNodes(unittest.TestCase):

    TEST_PORT = 5001

    def setUp(self):
        self.db_fd, self.db_filename = tempfile.mkstemp()
        config = {'DATABASE': 'sqlite://{}'.format(self.db_filename),
                  'TESTING': True}
        self.node = Node(config)
        self.client = self.node.app.test_client()


    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_filename)


    def test_ping(self):
        """
        The test node responds to a HEAD request.
        """
        rv = self.client.head('/')
        assert rv.status_code == 200


    def test_add_peer(self):
        """
        A node can be told about a peer.
        """
        peer_info = {'url': 'http://localhost:{}'.format(self.TEST_PORT + 1)}
        rv = self.client.post('/peer', data=json.dumps(peer_info))
        assert rv.status_code == 201

        data = json.loads(rv.data)
        rv = self.client.get('/peer/{}'.format(data['id']))
        assert rv.status_code == 200

