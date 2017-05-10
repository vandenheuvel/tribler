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
        self.edge_node_a = NetworkNode("61", self.driver)
        self.edge_node_b = NetworkNode("62", self.driver)
        self.fake_node = NetworkNode("0", self.driver)

    # Tests for the neighbor query

    def test_get_neighbors(self):
        # Arrange
        expected_result_focus = ["31", "32", "33", "34"]
        expected_result_fake = []
        # Act
        result_list_focus = self.focus_node.neighbor_keys
        result_list_fake = self.fake_node.neighbor_keys
        # Assert
        self.assertEqual(sorted(expected_result_focus), sorted(result_list_focus))
        self.assertEqual(sorted(expected_result_fake), sorted(result_list_fake))

    def test_get_neighbors_non_existent(self):
        # Arrange
        expected_result = []
        # Act
        result_list = self.fake_node.neighbor_keys
        # Assert
        self.assertEqual(sorted(expected_result), sorted(result_list))

    # Tests for the total up

    def test_total_up_init(self):
        # Act
        focus_up = self.focus_node.total_uploaded
        # Assert
        self.assertEqual(focus_up, -1)

    def test_total_up(self):
        # Act
        focus_up = self.focus_node.total_up()
        # Assert
        self.assertEqual(focus_up, 247)

    def test_total_up_only_up(self):
        # Act
        focus_up = self.edge_node_b.total_up()
        # Assert
        self.assertEqual(focus_up, 5)

    def test_total_up_only_down(self):
        # Act
        focus_up = self.edge_node_a.total_up()
        # Assert
        self.assertEqual(focus_up, 2)

    def test_total_up_fake(self):
        # Act
        focus_up = self.fake_node.total_up()
        # Assert
        self.assertEqual(focus_up, 0)

    # Tests for the total down

    def test_total_down_init(self):
        # Act
        focus_down = self.focus_node.total_downloaded
        # Assert
        self.assertEqual(focus_down, -1)

    def test_total_down(self):
        # Act
        focus_down = self.focus_node.total_down()
        # Assert
        self.assertEqual(focus_down, 963)

    def test_total_down_only_down(self):
        # Act
        focus_down = self.edge_node_a.total_down()
        # Assert
        self.assertEqual(focus_down, 10)

    def test_total_down_only_up(self):
        # Act
        focus_down = self.edge_node_b.total_down()
        # Assert
        self.assertEqual(focus_down, 1)

    def test_total_down_fake(self):
        # Act
        focus_down = self.fake_node.total_down()
        # Assert
        self.assertEqual(focus_down, 0)

    # Tests for neighbor up

    def test_neighbor_up(self):
        # Act
        neighbor_up = self.focus_node.neighbor_up("31")
        # Assert
        self.assertEqual(neighbor_up, 28)

    def test_neighbor_up_only_up(self):
        # Act
        focus_up = self.edge_node_b.neighbor_up("63")
        # Assert
        self.assertEqual(focus_up, 5)

    def test_neighbor_up_only_down(self):
        # Act
        focus_up = self.edge_node_a.neighbor_up("63")
        # Assert
        self.assertEqual(focus_up, 2)

    def test_neighbor_up_fake(self):
        # Act
        focus_up = self.fake_node.neighbor_up("30")
        # Assert
        self.assertEqual(focus_up, 0)

    # Tests for neighbor down

    def test_neighbor_down(self):
        # Act
        neighbor_down = self.focus_node.neighbor_down("31")
        # Assert
        self.assertEqual(neighbor_down, 54)

    def test_neighbor_down_only_down(self):
        # Act
        focus_down = self.edge_node_a.neighbor_down("63")
        # Assert
        self.assertEqual(focus_down, 10)

    def test_neighbor_down_only_up(self):
        # Act
        focus_down = self.edge_node_b.neighbor_down("63")
        # Assert
        self.assertEqual(focus_down, 1)

    def test_neighbor_down_fake(self):
        # Act
        focus_up = self.fake_node.neighbor_up("30")
        # Assert
        self.assertEqual(focus_up, 0)
