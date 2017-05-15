"""
This file contains the database connection used for the statistics display.
"""
import os

from twisted.internet.defer import inlineCallbacks

from Tribler.community.multichain.database import DATABASE_DIRECTORY
from Tribler.community.multichain.statistics.statistics_database import StatisticsDB
from Tribler.dispersy.util import blocking_call_on_reactor_thread
from Tribler.Test.Community.Multichain.test_multichain_utilities import TestBlock
from Tribler.Test.test_as_server import AbstractServer


class TestStatisticsDatabase(AbstractServer):

    def __init__(self, *args, **kwargs):
        super(TestStatisticsDatabase, self).__init__(*args, **kwargs)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, **kwargs):
        yield super(TestStatisticsDatabase, self).setUp()
        path = os.path.join(self.getStateDir(), DATABASE_DIRECTORY)
        if not os.path.exists(path):
            os.makedirs(path)
        self.db = StatisticsDB(self.getStateDir())
        self.block1 = TestBlock()
        self.block2 = TestBlock()

    @blocking_call_on_reactor_thread
    def test_total_down(self):
        self.db.add_block(self.block1)
        self.assertEqual(self.block1.total_up, self.db.total_up(self.block1.public_key))

    @blocking_call_on_reactor_thread
    def test_total_up(self):
        self.db.add_block(self.block2)
        self.assertEqual(self.block2.total_down, self.db.total_down(self.block2.public_key))

    @blocking_call_on_reactor_thread
    def test_neighbors(self):
        self.block1.link_public_key = self.block2.public_key
        self.db.add_block(self.block1)

        expected_result = {self.block2.public_key: {"up": self.block1.up, "down": self.block1.down}}

        self.assertDictEqual(expected_result, self.db.neighbor_list(self.block1.public_key))