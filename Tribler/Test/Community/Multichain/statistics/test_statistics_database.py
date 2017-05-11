"""
This file contains the test case for the statistics display.

Both the NetworkNode and the DbDriver are tested in this file.
"""
from twisted.internet.defer import inlineCallbacks

from Tribler.community.multichain.statistics.db_driver import DbDriver
from Tribler.community.multichain.statistics.network_node import NetworkNode
from Tribler.Test.test_as_server import BaseTestCase


class TestStatisticsDatabase(BaseTestCase):
    """
    Test class for the statistics display database connection.
    """

    @inlineCallbacks
    def setUp(self):
        """
        Setup for the test case.

        :return: test class for the database connection.
        """
        yield super(TestStatisticsDatabase, self).setUp()
        self.driver = DbDriver()
        self.focus_node = NetworkNode("30", self.driver)
        self.edge_node_a = NetworkNode("61", self.driver)
        self.edge_node_b = NetworkNode("62", self.driver)
        self.fake_node = NetworkNode("0", self.driver)

    def test_get_neighbors(self):
        """
        The network node should return the correct list of neighbors.
        """
        expected_result_focus = ["31", "32", "33", "34"]
        expected_result_fake = []

        result_list_focus = self.focus_node.neighbor_keys
        result_list_fake = self.fake_node.neighbor_keys

        self.assertEqual(sorted(expected_result_focus), sorted(result_list_focus))
        self.assertEqual(sorted(expected_result_fake), sorted(result_list_fake))

    def test_total_up(self):
        """
        The node should return the right amount of uploaded data.
        """
        focus_up = self.focus_node.total_uploaded
        self.assertEqual(focus_up, -1)

        focus_up = self.focus_node.total_up()
        self.assertEqual(focus_up, 247)

        only_up = self.edge_node_b.total_up()
        only_down = self.edge_node_a.total_up()
        fake_up = self.fake_node.total_up()

        self.assertEqual(only_up, 5)
        self.assertEqual(only_down, 2)
        self.assertEqual(fake_up, 0)

    def test_total_down(self):
        """
        The node should return the right amount of downloaded data.
        """
        focus_down = self.focus_node.total_downloaded
        self.assertEqual(focus_down, -1)

        focus_down = self.focus_node.total_down()
        self.assertEqual(focus_down, 963)

        only_down = self.edge_node_a.total_down()
        only_up = self.edge_node_b.total_down()
        fake_down = self.fake_node.total_down()

        self.assertEqual(only_down, 10)
        self.assertEqual(only_up, 1)
        self.assertEqual(fake_down, 0)

    def test_neighbor_up(self):
        """
        The node should return the right amount of data uploaded to a neighbor.
        """
        neighbor_up = self.focus_node.neighbor_up("31")
        self.assertEqual(neighbor_up, 28)

        focus_up = self.edge_node_b.neighbor_up("63")
        self.assertEqual(focus_up, 5)

        only_up = self.edge_node_a.neighbor_up("63")
        self.assertEqual(only_up, 2)

        fake_up = self.fake_node.neighbor_up("30")
        self.assertEqual(fake_up, 0)

    def test_neighbor_down(self):
        """
        The node should return the right amount of data downloaded from a neighbor.
        """
        focus_down = self.focus_node.neighbor_down("31")
        self.assertEqual(focus_down, 54)

        only_down = self.edge_node_a.neighbor_down("63")
        self.assertEqual(only_down, 10)

        only_up = self.edge_node_b.neighbor_down("63")
        self.assertEqual(only_up, 1)

        fake_up = self.fake_node.neighbor_up("30")
        self.assertEqual(fake_up, 0)
