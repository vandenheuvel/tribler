from Tribler.Test.test_as_server import BaseTestCase
from Tribler.community.multichain.StatisticsDisplay.networkNode import NetworkNode
from Tribler.community.multichain.StatisticsDisplay.dbDriver import DbDriver

from twisted.internet.defer import inlineCallbacks
from Tribler.dispersy.util import blocking_call_on_reactor_thread


class TestStatisticsDatabase(BaseTestCase):

    def __init__(self, *args, **kwargs):
        super(TestStatisticsDatabase, self).__init__(*args, **kwargs)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, **kwargs):
        yield super(TestStatisticsDatabase, self).setUp()
        self.driver = DbDriver()
        self.focus_node = NetworkNode("30", self.driver)  # hardcoded hex of focus node


    @blocking_call_on_reactor_thread
    def test_get_neighbors(self):
        # Arrange
        expected_result = ["31", "32", "33", "34"]
        # Act
        result_list = self.focus_node.neighbor_keys
        # Assert
        assert len(result_list) == len(expected_result)
        for key_hash in expected_result:
            if key_hash not in result_list:
                assert False, "Neighbor was not in list: %s" % key_hash

    @blocking_call_on_reactor_thread
    def test_total_up(self):
        # Act
        focus_up = self.focus_node.total_up()
        # Assert
        assert focus_up == 1224, "Total up other than expected: %d" % focus_up

    @blocking_call_on_reactor_thread
    def test_total_down(self):
        # Act
        focus_down = self.focus_node.total_down()
        # Assert
        assert focus_down == 3881, "Total down other than expected: %d" % focus_down

    @blocking_call_on_reactor_thread
    def test_neighbor_up(self):
        # Arrange
        neighbor_key = "31"
        # Act
        neighbor_up = self.focus_node.neighbor_up(neighbor_key)
        # Assert
        assert neighbor_up == 28, "Neighbor up other than expected: %d" % neighbor_up

    @blocking_call_on_reactor_thread
    def test_neighbor_down(self):
        # Arrange
        neighbor_key = "31"
        # Act
        neighbor_down = self.focus_node.neighbor_down(neighbor_key)
        # Assert
        assert neighbor_down == 54, "Neighbor down other than expected: %d" % neighbor_down

    @blocking_call_on_reactor_thread
    def test_neighbor_up_not_neighbor(self):
        # Arrange
        neighbor_key = "41"
        # Act
        neighbor_up = self.focus_node.neighbor_up(neighbor_key)
        # Assert
        assert neighbor_up == 0, "Neighbor up other than expected: %d" % neighbor_up
