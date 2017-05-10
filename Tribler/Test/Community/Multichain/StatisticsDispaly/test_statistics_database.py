"""
This file contains the test case for the statistics display.
Both the NetworkNode and the DbDriver are tested in this file.
"""

from twisted.internet.defer import inlineCallbacks

from Tribler.community.multichain.StatisticsDisplay.dbDriver import DbDriver
from Tribler.community.multichain.StatisticsDisplay.networkNode import NetworkNode
from Tribler.Test.test_as_server import BaseTestCase


class TestStatisticsDatabase(BaseTestCase):
    """
    Test class for the statistics display database connection.
    """
    def __init__(self, *args, **kwargs):
        """
        Default init used for the BaseTestCase.

        :param args: run arguments.
        :param kwargs: dictionary containing values for the arguments
        """
        super(TestStatisticsDatabase, self).__init__(*args, **kwargs)

    @inlineCallbacks
    def setUp(self):
        """
        Setup for the test case.

        :return: test class for the database connection.
        """
        yield super(TestStatisticsDatabase, self).setUp()
        self.driver = DbDriver()
        self.focus_node = NetworkNode("30", self.driver)  # hardcoded hex of focus node

    def test_get_neighbors(self):
        # Arrange
        expected_result = ["31", "32", "33", "34"]
        # Act
        result_list = self.focus_node.neighbor_keys
        # Assert
        self.assertEqual(sorted(expected_result), sorted(result_list), "List of neighbors in other than expected")

    def test_total_up(self):
        # Act
        focus_up = self.focus_node.total_up()
        # Assert
        self.assertEqual(focus_up, 1224, "Total up other than expected: %d" % focus_up)

    def test_total_down(self):
        # Act
        focus_down = self.focus_node.total_down()
        # Assert
        self.assertEqual(focus_down, 3881, "Total down other than expected: %d" % focus_down)

    def test_neighbor_up(self):
        # Arrange
        neighbor_key = "31"
        # Act
        neighbor_up = self.focus_node.neighbor_up(neighbor_key)
        # Assert
        self.assertEqual(neighbor_up, 28, "Neighbor up other than expected: %d" % neighbor_up)

    def test_neighbor_down(self):
        # Arrange
        neighbor_key = "31"
        # Act
        neighbor_down = self.focus_node.neighbor_down(neighbor_key)
        # Assert
        self.assertEqual(neighbor_down, 54, "Neighbor down other than expected: %d" % neighbor_down)

    def test_neighbor_up_not_neighbor(self):
        # Arrange
        neighbor_key = "41"
        # Act
        neighbor_up = self.focus_node.neighbor_up(neighbor_key)
        # Assert
        self.assertEqual(neighbor_up, 0, "Neighbor up other than expected: %d" % neighbor_up)
