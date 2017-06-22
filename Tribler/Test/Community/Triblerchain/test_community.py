from Tribler.Test.Community.Trustchain.test_community import BaseTestTrustChainCommunity
from Tribler.Test.Community.Trustchain.test_trustchain_utilities import TrustChainTestCase
from Tribler.community.triblerchain.block import TriblerChainBlock
from Tribler.community.triblerchain.community import TriblerChainCommunity, PendingBytes, TriblerChainCommunityCrawler
from Tribler.community.trustchain.community import HALF_BLOCK, CRAWL
from Tribler.community.tunnel.routing import Circuit
from Tribler.dispersy.requestcache import IntroductionRequestCache
from Tribler.dispersy.tests.dispersytestclass import DispersyTestFunc
from Tribler.dispersy.util import blocking_call_on_reactor_thread
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import deferLater


class TestPendingBytes(TrustChainTestCase):
    """
    This class contains tests for the PendingBytes object
    """

    def test_add_pending_bytes(self):
        """
        Test adding to pending bytes
        """
        pending_bytes = PendingBytes(20, 30)
        self.assertTrue(pending_bytes.add(20, 30))
        self.assertFalse(pending_bytes.add(-100, -100))


class TestTriblerChainCommunity(BaseTestTrustChainCommunity):
    """
    Class that tests the TriblerChainCommunity on an integration level.
    """

    @staticmethod
    def set_expectation(node, req, up, down):
        node.community.pending_bytes[req.community.my_member.public_key] = PendingBytes(down, up)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def create_nodes(self, *args, **kwargs):
        nodes = yield DispersyTestFunc.create_nodes(self, *args, community_class=TriblerChainCommunity,
                                                    memory_database=False, **kwargs)
        for outer in nodes:
            for inner in nodes:
                if outer != inner:
                    outer.send_identity(inner)

        returnValue(nodes)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_cleanup_pending_bytes(self):
        """
        Test cleaning of pending bytes
        """
        node, = yield self.create_nodes(1)
        node.community.pending_bytes['a'] = 1234
        self.assertIn('a', node.community.pending_bytes)
        node.community.cleanup_pending('a')
        self.assertNotIn('a', node.community.pending_bytes)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_on_tunnel_remove(self):
        """
        Test the on_tunnel_remove handler function for a circuit
        """
        # Arrange
        node, other = yield self.create_nodes(2)
        tunnel_node = Circuit(long(0), 0)
        tunnel_other = Circuit(long(0), 0)
        tunnel_node.bytes_up = tunnel_other.bytes_down = 12 * 1024 * 1024
        tunnel_node.bytes_down = tunnel_other.bytes_up = 14 * 1024 * 1024

        # Act
        node.call(node.community.on_tunnel_remove, None, None, tunnel_node, self._create_target(node, other))
        other.call(other.community.on_tunnel_remove, None, None, tunnel_other, self._create_target(other, node))
        yield deferLater(reactor, 5.1, lambda: None)

        # Assert
        _, signature_request = node.receive_message(names=[HALF_BLOCK]).next()
        node.give_message(signature_request, other)
        yield deferLater(reactor, 0.1, lambda: None)
        _, signature_request = other.receive_message(names=[HALF_BLOCK]).next()
        other.give_message(signature_request, node)
        yield deferLater(reactor, 0.1, lambda: None)

        self.assertBlocksInDatabase(node, 2)
        self.assertBlocksInDatabase(other, 2)
        self.assertBlocksAreEqual(node, other)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_on_tunnel_remove_small(self):
        """
        Test the on_tunnel_remove handler function for a circuit
        """
        # Arrange
        node, other = yield self.create_nodes(2)
        tunnel_node = Circuit(long(0), 0)
        tunnel_other = Circuit(long(0), 0)
        tunnel_node.bytes_up = tunnel_other.bytes_down = 1024
        tunnel_node.bytes_down = tunnel_other.bytes_up = 2 * 1024

        # Act
        node.call(node.community.on_tunnel_remove, None, None, tunnel_node, self._create_target(node, other))
        other.call(other.community.on_tunnel_remove, None, None, tunnel_other, self._create_target(other, node))
        yield deferLater(reactor, 5.1, lambda: None)

        # Assert
        with self.assertRaises(StopIteration):
            self.assertFalse(node.receive_message(names=[HALF_BLOCK]).next())

        with self.assertRaises(StopIteration):
            self.assertFalse(other.receive_message(names=[HALF_BLOCK]).next())

        self.assertBlocksInDatabase(node, 0)
        self.assertBlocksInDatabase(other, 0)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_on_tunnel_remove_append_pending(self):
        """
        Test the on_tunnel_remove handler function for a circuit
        """
        # Arrange
        node, other = yield self.create_nodes(2)
        tunnel_node = Circuit(long(0), 0)
        tunnel_node.bytes_up = 12 * 1024 * 1024
        tunnel_node.bytes_down = 14 * 1024 * 1024

        # Act
        node.call(node.community.on_tunnel_remove, None, None, tunnel_node, self._create_target(node, other))
        node.call(node.community.on_tunnel_remove, None, None, tunnel_node, self._create_target(node, other))
        yield deferLater(reactor, 5.1, lambda: None)

        self.assertEqual(node.community.pending_bytes[other.community.my_member.public_key].up, 2*tunnel_node.bytes_up)
        self.assertEqual(node.community.pending_bytes[other.community.my_member.public_key].down,
                         2*tunnel_node.bytes_down)

    def test_receive_request_invalid(self):
        """
        Test the community to receive a request message.
        """
        # Arrange
        node, other = self.create_nodes(2)
        target_other = self._create_target(node, other)
        TestTriblerChainCommunity.set_expectation(other, node, 10, 5)
        transaction = {"up": 10, "down": 5}
        node.call(node.community.sign_block, target_other, other.my_member.public_key, transaction)
        _, block_req = other.receive_message(names=[HALF_BLOCK]).next()
        # Act
        # construct faked block
        block = block_req.payload.block
        block.transaction["up"] += 10
        block.transaction["total_up"] = block.transaction["up"]
        block_req = node.community.get_meta_message(HALF_BLOCK).impl(
            authentication=tuple(),
            distribution=(node.community.claim_global_time(),),
            destination=(target_other,),
            payload=(block,))
        other.give_message(block_req, node)

        # Assert
        self.assertBlocksInDatabase(other, 0)
        self.assertBlocksInDatabase(node, 1)

        with self.assertRaises(StopIteration):
            # No signature responses, or crawl requests should have been sent
            node.receive_message(names=[HALF_BLOCK, CRAWL]).next()

    def test_receive_request_twice(self):
        """
        Test the community to receive a request message twice.
        """
        # Arrange
        node, other = self.create_nodes(2)
        target_other = self._create_target(node, other)
        transaction = {"up": 10, "down": 5}
        TestTriblerChainCommunity.set_expectation(node, other, 50, 50)
        TestTriblerChainCommunity.set_expectation(other, node, 50, 50)
        TestTriblerChainCommunity.create_block(node, other, target_other, transaction)

        # construct faked block
        block = node.call(node.community.persistence.get_latest, node.my_member.public_key)
        block_req = node.community.get_meta_message(HALF_BLOCK).impl(
            authentication=tuple(),
            distribution=(node.community.claim_global_time(),),
            destination=(target_other,),
            payload=(block,))
        other.give_message(block_req, node)

        # Assert
        self.assertBlocksInDatabase(other, 2)
        self.assertBlocksInDatabase(node, 2)

        with self.assertRaises(StopIteration):
            # No signature responses, or crawl requests should have been sent
            node.receive_message(names=[HALF_BLOCK, CRAWL]).next()

    def test_receive_request_too_much(self):
        """
        Test the community to receive a request that claims more than we are prepared to sign
        """
        # Arrange
        node, other = self.create_nodes(2)
        target_other = self._create_target(node, other)
        TestTriblerChainCommunity.set_expectation(other, node, 3, 3)
        transaction = {"up": 10, "down": 5}
        node.call(node.community.sign_block, target_other, other.my_member.public_key, transaction)
        # Act
        other.give_message(other.receive_message(names=[HALF_BLOCK]).next()[1], node)

        # Assert
        self.assertBlocksInDatabase(other, 1)
        self.assertBlocksInDatabase(node, 1)

        with self.assertRaises(StopIteration):
            # No signature responses, or crawl requests should have been sent
            node.receive_message(names=[HALF_BLOCK, CRAWL]).next()

    def test_receive_request_unknown_pend(self):
        """
        Test the community to receive a request that claims about a peer we know nothing about
        """
        # Arrange
        node, other = self.create_nodes(2)
        target_other = self._create_target(node, other)
        transaction = {"up": 10, "down": 5}
        node.call(node.community.sign_block, target_other, other.my_member.public_key, transaction)
        # Act
        other.give_message(other.receive_message(names=[HALF_BLOCK]).next()[1], node)

        # Assert
        self.assertBlocksInDatabase(other, 1)
        self.assertBlocksInDatabase(node, 1)

        with self.assertRaises(StopIteration):
            # No signature responses, or crawl requests should have been sent
            node.receive_message(names=[HALF_BLOCK, CRAWL]).next()

    def test_block_values(self):
        """
        If a block is created between two nodes both
        should have the correct total_up and total_down of the signature request.
        """
        # Arrange
        node, other = self.create_nodes(2)
        TestTriblerChainCommunity.set_expectation(node, other, 50, 50)
        TestTriblerChainCommunity.set_expectation(other, node, 50, 50)
        transaction = {"up": 10, "down": 5}

        # Act
        TestTriblerChainCommunity.create_block(node, other, self._create_target(node, other), transaction)

        # Assert
        block = node.call(TriblerChainBlock.create, transaction, node.community.persistence,
                          node.community.my_member.public_key)
        self.assertEqual(20, block.transaction["total_up"])
        self.assertEqual(10, block.transaction["total_down"])
        block = other.call(TriblerChainBlock.create, transaction, other.community.persistence,
                           other.community.my_member.public_key)
        self.assertEqual(15, block.transaction["total_up"])
        self.assertEqual(15, block.transaction["total_down"])

    def test_block_values_after_request(self):
        """
        After a request is sent, a node should update its totals.
        """
        # Arrange
        node, other = self.create_nodes(2)
        transaction = {"up": 10, "down": 5}
        node.call(node.community.sign_block, self._create_target(node, other), other.my_member.public_key, transaction)

        # Assert
        block = node.call(TriblerChainBlock.create, transaction, node.community.persistence,
                          node.community.my_member.public_key)
        self.assertEqual(20, block.transaction["total_up"])
        self.assertEqual(10, block.transaction["total_down"])

    def test_crawler_on_introduction_received(self):
        """
        Test the crawler takes a step when an introduction is made by the walker
        """
        # Arrange
        TriblerChainCommunityCrawler.CrawlerDelay = 10000000
        crawler = DispersyTestFunc.create_nodes(self, 1, community_class=TriblerChainCommunityCrawler,
                                                memory_database=False)[0]
        node, = self.create_nodes(1)
        node._community.cancel_pending_task("take fast steps")
        node._community.cancel_pending_task("take step")
        node._community.cancel_pending_task("start_walking")
        target_node_from_crawler = self._create_target(node, crawler)

        # when we call on_introduction request it is going to forward the argument to it's super implementation.
        # Dispersy will error if it does not expect this, and the target code will not be tested. So we pick at
        # dispersy's brains to make it accept the intro response.
        intro_request_info = crawler.call(IntroductionRequestCache, crawler.community, None)
        intro_response = node.create_introduction_response(target_node_from_crawler, node.lan_address, node.wan_address,
                                                           node.lan_address, node.wan_address,
                                                           u"unknown", False, intro_request_info.number)
        intro_response._candidate = target_node_from_crawler
        crawler.community.request_cache._identifiers[
            crawler.community.request_cache._create_identifier(intro_request_info.number, u"introduction-request")
        ] = intro_request_info

        # and we don't actually want to send the crawl request since the counter party is fake, just count if it is run
        counter = [0]

        def replacement(cand, pk):
            counter[0] += 1
        crawler._community.send_crawl_request = replacement

        # Act
        crawler.call(crawler.community.on_introduction_response, [intro_response])

        # Assert
        self.assertEqual(counter[0], 1)

    def test_get_statistics_no_blocks(self):
        """
        Test the get_statistics method where last block is none
        """
        node, = self.create_nodes(1)
        statistics = node.community.get_statistics()
        assert isinstance(statistics, dict), type(statistics)
        assert len(statistics) > 0

    def test_get_statistics_with_previous_block(self):
        """
        Test the get_statistics method where a last block exists
        """
        # Arrange
        node, other = self.create_nodes(2)
        transaction = {"up": 10, "down": 5}
        TestTriblerChainCommunity.create_block(node, other, self._create_target(node, other), transaction)

        # Get statistics
        statistics = node.community.get_statistics()
        assert isinstance(statistics, dict), type(statistics)
        assert len(statistics) > 0

    def test_get_statistics_for_not_self(self):
        """
        Test the get_statistics method where a last block exists
        """
        # Arrange
        node, other = self.create_nodes(2)
        transaction = {"up": 10, "down": 5}
        TestTriblerChainCommunity.create_block(node, other, self._create_target(node, other), transaction)

        # Get statistics
        statistics = node.community.get_statistics(public_key=other.community.my_member.public_key)
        assert isinstance(statistics, dict), type(statistics)
        assert len(statistics) > 0

    def test_get_node_empty(self):
        """
        Check whether get_node returns the correct node if no past data is given.
        """
        node, = self.create_nodes(1)
        self.assertEqual({"total_up": 3, "total_down": 5, "total_neighbors": 2},
                         node.community.get_node("test", [], 3, 5, 2))

    def test_get_node_maximum(self):
        """
        Check whether get_node returns the maximum of total_up and total_down.
        """
        node, = self.create_nodes(1)
        nodes = {"test": {"total_up": 1, "total_down": 10, "total_neighbors": 2}}
        self.assertEqual({"total_up": 3, "total_down": 10, "total_neighbors": 2},
                         node.community.get_node("test", nodes, 3, 5, 1))

    def test_get_node_request_total_traffic(self):
        """
        Check whether get_node requires a total_traffic method if no total_up and total_down is given.
        """
        node, = self.create_nodes(1)
        node.community.persistence.total_traffic = lambda _: [5, 6, 2]
        self.assertEqual({"total_up": 5, "total_down": 6, "total_neighbors": 2},
                         node.community.get_node('74657374', []))

    def test_format_edges(self):
        """
        Verify whether format_edges returns the correct nodes and edges
        """
        node, = self.create_nodes(1)
        edge_list = [
            # [pk_a, pk_b, a->b, b->a, a_up, a_down, a_neighbors]
            ("aa", "bb", 10, 15, 10, 15, 1),
            ("bb", "cc", 8, 3, 23, 13, 2)
        ]
        node.community.persistence.get_graph_edges = lambda _1, _2: edge_list
        node.community.persistence.total_traffic = lambda pk: (0, 0, 1)

        expected_nodes = {
            "aa": {"total_up": 10, "total_down": 15, "total_neighbors": 1},
            "bb": {"total_up": 23, "total_down": 13, "total_neighbors": 2},
            "cc": {"total_up": 0, "total_down": 0, "total_neighbors": 1}
        }

        expected_edges = {
            "aa": [("bb", 10, 15)],
            "bb": [("aa", 15, 10), ("cc", 8, 3)],
            "cc": [("bb", 3, 8)]
        }

        nodes, edges = node.community.format_edges("aa", 2)
        self.assertDictEqual(nodes, expected_nodes)
        self.assertDictEqual(expected_edges, edges)

    def test_get_graph_no_edges(self):
        """
        Verify whether get_graph returns a correct result if no edges are present.
        """
        node, = self.create_nodes(1)
        nodes = {
            "aa": {"total_up": 0, "total_down": 0, "total_neighbors": 0}
        }
        edges = {}

        node.community.format_edges = lambda _1, _2: (nodes, edges)

        expected_nodes = [
            {"public_key": "aa", "total_up": 0, "total_down": 0, "total_neighbors": 0, "score": 0.5}
        ]
        expected_edges = []

        actual_nodes, actual_edges = node.community.get_graph("aa", 2, 0, [])
        self.assertListEqual(expected_nodes, actual_nodes)
        self.assertListEqual(expected_edges, actual_edges)

    def test_get_graph(self):
        """
        Verify whether get_graph returns a correct list of nodes and edges
        """
        node, = self.create_nodes(1)
        nodes = {
            "aa": {"total_up": 0, "total_down": 0, "total_neighbors": 2},
            "bb": {"total_up": 1, "total_down": 1, "total_neighbors": 5},
            "cc": {"total_up": 2, "total_down": 2, "total_neighbors": 2},
            "dd": {"total_up": 3, "total_down": 3, "total_neighbors": 1},
            "ee": {"total_up": 4, "total_down": 4, "total_neighbors": 1},
            "ff": {"total_up": 5, "total_down": 5, "total_neighbors": 1}
        }
        edges = {
            "aa": [("bb", 0, 0), ("cc", 0, 0), ("ff", 0, 0)],
            "bb": [("aa", 0, 0), ("cc", 0, 0), ("ee", 0, 0), ("ff", 0, 0), ("dd", 0, 0)],
            "cc": [("aa", 0, 0), ("bb", 0, 0)],
        }

        node.community.format_edges = lambda _1, _2: (nodes, edges)

        expected_nodes = [
            {"public_key": "aa", "total_up": 0, "total_down": 0, "total_neighbors": 2, "score": 0.5},
            {"public_key": "bb", "total_up": 1, "total_down": 1, "total_neighbors": 5, "score": 0.5},
            {"public_key": "cc", "total_up": 2, "total_down": 2, "total_neighbors": 2, "score": 0.5},
        ]
        expected_edges = [
            {"from": "aa", "to": "bb", "amount": 0},
            {"from": "bb", "to": "aa", "amount": 0},
            {"from": "aa", "to": "cc", "amount": 0},
            {"from": "cc", "to": "aa", "amount": 0},
            {"from": "bb", "to": "cc", "amount": 0},
            {"from": "cc", "to": "bb", "amount": 0},
        ]

        actual_nodes, actual_edges = node.community.get_graph("aa", 1, 1, ["cc"])
        self.assertItemsEqual(expected_nodes, actual_nodes)
        self.assertItemsEqual(expected_edges, actual_edges)

    def test_get_graph_circular(self):
        """
        Verify whether get_graph returns a correct list of nodes and edges when of circular form
        """
        node, = self.create_nodes(1)
        nodes = {
            "aa": {"total_up": 0, "total_down": 0, "total_neighbors": 2},
            "bb": {"total_up": 1, "total_down": 1, "total_neighbors": 5},
            "cc": {"total_up": 2, "total_down": 2, "total_neighbors": 2},
        }
        edges = {
            "aa": [("bb", 0, 0), ("cc", 0, 0)],
            "bb": [("aa", 0, 0), ("cc", 0, 0)],
            "cc": [("aa", 0, 0), ("bb", 0, 0)]
        }

        node.community.format_edges = lambda _1, _2: (nodes, edges)

        expected_nodes = [
            {"public_key": "aa", "total_up": 0, "total_down": 0, "total_neighbors": 2, "score": 0.5},
            {"public_key": "bb", "total_up": 1, "total_down": 1, "total_neighbors": 5, "score": 0.5},
            {"public_key": "cc", "total_up": 2, "total_down": 2, "total_neighbors": 2, "score": 0.5},
        ]
        expected_edges = [
            {"from": "aa", "to": "bb", "amount": 0},
            {"from": "bb", "to": "aa", "amount": 0},
            {"from": "aa", "to": "cc", "amount": 0},
            {"from": "cc", "to": "aa", "amount": 0},
            {"from": "bb", "to": "cc", "amount": 0},
            {"from": "cc", "to": "bb", "amount": 0},
        ]

        actual_nodes, actual_edges = node.community.get_graph("aa", 1, 2, [])
        self.assertItemsEqual(expected_nodes, actual_nodes)
        self.assertItemsEqual(expected_edges, actual_edges)

