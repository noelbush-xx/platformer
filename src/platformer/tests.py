from multiprocessing import Process
from unittest import TestCase

import requests

from .node import app


class NodeTests(TestCase):

    TEST_PORT = 5000

    def setUp(self):
        self.node = Process(target=app.run, kwargs={'port': self.TEST_PORT})
        self.node.start()


    def tearDown(self):
        self.node.terminate()


    def test_ping(self):
        r = requests.head('http://localhost:{}'.format(self.TEST_PORT))
        assert r.status_code == 200
