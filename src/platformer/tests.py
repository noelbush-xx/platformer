import json
import logging
from multiprocessing import Process
import os
from os.path import abspath, dirname, join
import requests
import subprocess
import sys
import tempfile
from time import sleep
import unittest

from platformer import Node


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CouldNotStartPeerApp(Exception):

    def __init__(self, url):
        self.url = url


    def __str__(self):
        return ('Could not start peer app listening at {} '
                ' within configured time limit.'.format(url))


def start_node(name, port):
    peer = Node(name, reinit_db=True)
    return start_node_app(peer, port)


def start_node_app(peer, port):
    peer_proc = Process(target=peer.app.run, kwargs={'port': port})
    logger.debug('Starting node app on port {}.'.format(port))
    peer_proc.start()

    peer_url = 'http://localhost:{}'.format(port)

    # Give the app time to start.
    wait, success = 2.0, False
    while not success and wait > 0.0:
        try:
            response = requests.get(peer_url)
            success = True
        except:
            wait -= 0.1
            sleep(0.1)

    if not success:
        raise

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
        response = self.client.head('/')
        assert response.status_code == 200


    def test_add_peer(self):
        """
        A node can be told about a peer.
        """
        peer_info = {'url': 'http://localhost:{}'.format(self.TEST_PORT + 1)}
        response = self.client.post('/peer', data=json.dumps(peer_info))
        assert response.status_code == 201

        post_response = json.loads(response.data)
        response = self.client.get('/peer/{}'.format(post_response['id']))
        assert response.status_code == 200

        get_response = json.loads(response.data)
        assert get_response['url'] == peer_info['url']


    def test_is_me(self):
        """
        A node can determine that a purported peer is, in fact, itself.
        """
        try:
            peer, peer_proc, peer_url = start_node('test_01', self.TEST_PORT)
            assert peer.is_me(peer_url)
        finally:
            peer_proc.terminate()


    def test_check_peer(self):
        """
        A node can check on an existing peer.
        """
        try:
            peer, peer_proc, peer_url = start_node('test_01', self.TEST_PORT)
            assert self.node.check_peer(peer_url)

            # Check again -- the second time should (transparently to us)
            # cause our node to find an existing record and merely update it.
            assert self.node.check_peer(peer_url)
        finally:
            peer_proc.terminate()


    def test_peer_lists(self):
        """
        Nodes can get lists of peers from one another.
        """
        PEER_COUNT = 5
        peers = []
        try:
            # Create some other nodes and tell our node about them.
            for n in xrange(1, PEER_COUNT + 1):
                peer, peer_proc, peer_url = start_node('test_{}'.format(n),
                                                       self.TEST_PORT + n)
                peers.append((peer, peer_proc, peer_url))
                self.client.post('/peer', data=json.dumps({'url': peer_url}))

            # Verify that our node has the list of the 10 others.
            logger.debug('Verifying list of peers from test node.')
            response = self.client.get('/peer')
            get_response = json.loads(response.data)
            assert len(get_response['objects']) == PEER_COUNT

            # Now tell each node to talk to our node and get its list of peers.
            # (For this we have to start our own node's app.)
            _, node_proc, node_url = start_node_app(self.node, self.TEST_PORT)
            for peer, _, peer_url in peers:
                logger.debug("Asking peer at {} to get test node's list "
                             "of peers.".format(peer_url))
                peer.get_peer_list_from(node_url)

                # Now verify that the peer has the full list of *PEER_COUNT - 1*
                # peers (it should have excluded itself).
                response = requests.get('{}/peer'.format(peer_url))
                get_response = json.loads(response.content)
                assert len(get_response['objects']) == PEER_COUNT - 1

        finally:
            logger.debug('Terminating test node and peers.')
            node_proc.terminate()
            for _, peer_proc, _ in peers:
                peer_proc.terminate()
