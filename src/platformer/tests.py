import json
from multiprocessing import Process
import os
from os.path import abspath, dirname, join
import subprocess
import sys
import tempfile
from time import sleep
import unittest

from platformer import Node


def start_peer(name, port):
    peer = Node(name, reinit_db=True)
    peer_proc = Process(target=peer.app.run, kwargs={'port': port})
    peer_proc.start()

    peer_url = 'http://localhost:{}'.format(port)

    return peer, peer_proc, peer_url


class TestNodes(unittest.TestCase):

    # When tests need to create "real" nodes that listen on a web interface,
    # this is the first port number to use (more will be created consecutively).
    TEST_PORT = 5001

    def setUp(self):
        self.db_fd, self.db_filename = tempfile.mkstemp()
        config = {'DATABASE': 'sqlite://{}'.format(self.db_filename),
                  'TESTING': True}
        self.node = Node('test', config)
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

        post_response = json.loads(rv.data)
        rv = self.client.get('/peer/{}'.format(post_response['id']))
        assert rv.status_code == 200

        get_response = json.loads(rv.data)
        assert get_response['url'] == peer_info['url']


    def test_check_peer(self):
        """
        A node can check on an existing peer.
        """
        try:
            peer, peer_proc, peer_url = start_peer('test_01', self.TEST_PORT)
            assert self.node.check_peer(peer_url)
        finally:
            peer_proc.terminate()

