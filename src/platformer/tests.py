import json
import os
from os.path import abspath, dirname, join
import subprocess
import sys
import tempfile
from time import sleep
import unittest

import platformer


class TestNodes(unittest.TestCase):

    TEST_PORT = 5001

    def setUp(self):
        self.db_fd, self.db_filename = tempfile.mkstemp()
        platformer.app.config['DATABASE'] = 'sqlite://{}'.format(self.db_filename)
        platformer.app.config['TESTING'] = True
        platformer.setup_app()
        self.app = platformer.app.test_client()


    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_filename)


    def test_ping(self):
        """
        The test node responds to a HEAD request.
        """
        rv = self.app.head('/')
        assert rv.status_code == 200


    def test_add_peer(self):
        """
        A node can be told about a peer.
        """
        peer_info = {'url': 'http://localhost:{}'.format(self.TEST_PORT + 1)}
        rv = self.app.post('/peer', data=json.dumps(peer_info))
        assert rv.status_code == 201, rv.data


