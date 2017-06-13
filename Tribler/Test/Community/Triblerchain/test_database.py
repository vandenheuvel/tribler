from binascii import hexlify, unhexlify
import os

from twisted.internet.defer import inlineCallbacks

from Tribler.Test.Community.Trustchain.test_trustchain_utilities import TrustChainTestCase, TestBlock
from Tribler.community.triblerchain.database import TriblerChainDB
from Tribler.community.trustchain.database import DATABASE_DIRECTORY
from Tribler.dispersy.util import blocking_call_on_reactor_thread


class TestDatabase(TrustChainTestCase):
    """
    Tests the Database for TriblerChain database.
    """

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, annotate=True):
        yield super(TestDatabase, self).setUp(annotate=annotate)
        path = os.path.join(self.getStateDir(), DATABASE_DIRECTORY)
        if not os.path.exists(path):
            os.makedirs(path)
        self.db = TriblerChainDB(self.getStateDir(), u'triblerchain')
        self.block1 = TestBlock(transaction={'up': 42, 'down': 13})
        self.block2 = TestBlock(transaction={'up': 46, 'down': 12})
        self.block3 = TestBlock(transaction={'up': 11, 'down': 23})

    @blocking_call_on_reactor_thread
    def test_get_num_interactors(self):
        """
        Test whether the right number of interactors is returned
        """
        self.block2 = TestBlock(previous=self.block1, transaction={'up': 42, 'down': 42})
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.assertEqual((2, 2), self.db.get_num_unique_interactors(self.block1.public_key))

    @blocking_call_on_reactor_thread
    def test_insert_aggregate_block(self):
        """
        Test whether statistics blocks are inserted correctly.
        """
        self.block1.public_key = unhexlify("00")
        self.block1.link_public_key = unhexlify("ff")
        self.db.insert_aggregate_block(self.block1)

        # Test for the first block
        rows = self.db.execute(
            u"SELECT public_key_a, public_key_b, traffic_a_to_b, traffic_b_to_a FROM triblerchain_aggregates", ()
        ).fetchall()

        self.assertEqual(len(rows), 1)

        row = rows[0]
        self.assertEqual(hexlify(self.block1.public_key), str(row[0]))
        self.assertEqual(hexlify(self.block1.link_public_key), str(row[1]))
        self.assertEqual(self.block1.transaction["up"], row[2])
        self.assertEqual(self.block1.transaction["down"], row[3])

        # Test after adding second block between same users
        self.block2.public_key = self.block1.link_public_key
        self.block2.link_public_key = self.block1.public_key
        self.db.insert_aggregate_block(self.block2)

        rows = self.db.execute(
            u"SELECT public_key_a, public_key_b, traffic_a_to_b, traffic_b_to_a FROM triblerchain_aggregates", ()
        ).fetchall()

        self.assertEqual(len(rows), 1)

        row = rows[0]
        self.assertEqual(hexlify(self.block1.public_key), str(row[0]))
        self.assertEqual(hexlify(self.block1.link_public_key), str(row[1]))
        self.assertEqual(self.block1.transaction["up"] + self.block2.transaction["down"], row[2])
        self.assertEqual(self.block1.transaction["down"] + self.block2.transaction["up"], row[3])

    @blocking_call_on_reactor_thread
    def test_total_traffic(self):
        """
        Test whether the correct amount of traffic is returned.
        """
        self.block1.public_key = unhexlify("00")
        self.block1.link_public_key = unhexlify("11")
        self.block2.public_key = unhexlify("11")
        self.block2.link_public_key = unhexlify("22")
        self.block3.public_key = unhexlify("ff")
        self.block3.link_public_key = unhexlify("33")

        self.db.insert_aggregate_block(self.block1)
        self.db.insert_aggregate_block(self.block2)
        self.db.insert_aggregate_block(self.block3)

        pk_1_up, pk_1_down = self.db.total_traffic("11")
        pk_f_up, pk_f_down = self.db.total_traffic("ff")
        fake_up, fake_down = self.db.total_traffic("aa")

        # Multiple links
        self.assertEqual(self.block1.transaction["down"] + self.block2.transaction["up"], pk_1_up)
        self.assertEqual(self.block1.transaction["up"] + self.block2.transaction["down"], pk_1_down)
        # One link
        self.assertEqual(self.block3.transaction["up"], pk_f_up)
        self.assertEqual(self.block3.transaction["down"], pk_f_down)
        # No links
        self.assertEqual(0, fake_up)
        self.assertEqual(0, fake_down)

    @blocking_call_on_reactor_thread
    def test_neighbors(self):
        """
        The database should return the correct list of neighbors and the traffic to and from them.
        """
        extra_block = TestBlock()
        extra_block.transaction = {"up": 0, "down": 0}

        # 00 -> 11, 11 -> 22, 22 -> 33, 33 -> 44
        self.block1.public_key = unhexlify("00")
        self.block1.link_public_key = unhexlify("11")
        self.block2.public_key = unhexlify("11")
        self.block2.link_public_key = unhexlify("22")
        self.block3.public_key = unhexlify("22")
        self.block3.link_public_key = unhexlify("33")
        extra_block.public_key = unhexlify("33")
        extra_block.link_public_key = unhexlify("44")

        # Add all blocks
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.db.add_block(self.block3)
        self.db.add_block(extra_block)

        expected_result = [
            ["00", "11", 42, 13, 42, 13],
            ["11", "22", 46, 12, 59, 54],
            ["22", "33", 11, 23, 23, 69]
        ]

        result = [[str(row[0]), str(row[1]), row[2], row[3], row[4], row[5]]
                  for row in self.db.get_graph_edges("11", neighbor_level=2)]

        self.assertEqual(expected_result, result)

    @blocking_call_on_reactor_thread
    def test_random_dummy_data(self):
        """
        The database should contain 104 rows when random dummy data is used.
        """
        self.db.use_dummy_data(use_random=True)

        num_rows = self.db.execute(u"SELECT count (*) FROM triblerchain_aggregates").fetchone()[0]
        self.assertEqual(num_rows, 52)
        self.assertTrue(self.db.dummy_setup)

    @blocking_call_on_reactor_thread
    def test_static_dummy_data(self):
        """
        The database should contain the fixed data set when non-random dummy data is used.
        """
        self.db.use_dummy_data(use_random=False)

        num_rows = self.db.execute(u"SELECT count (*) FROM triblerchain_aggregates").fetchone()[0]
        self.assertEqual(num_rows, 14)
        self.assertTrue(self.db.dummy_setup)

    @blocking_call_on_reactor_thread
    def test_no_dummy_overwrite(self):
        """
        The database should not overwrite the dataset once it has changed to dummy data.
        """
        self.db.use_dummy_data(use_random=True)

        focus_neighbors = self.db.get_graph_edges("00", 2)
        num_rows = self.db.execute(u"SELECT count (*) FROM triblerchain_aggregates").fetchone()[0]
        self.assertEqual(num_rows, 52)
        self.assertTrue(self.db.dummy_setup)

        # Database stays the same when trying to setup static data
        self.db.use_dummy_data(use_random=False)
        self.assertEqual(num_rows, 52)
        self.assertTrue(self.db.dummy_setup)

        # Database does not overwrite random data on second call
        self.db.use_dummy_data(use_random=True)
        self.assertEqual(num_rows, 52)
        self.assertTrue(self.db.dummy_setup)
        self.assertListEqual(focus_neighbors, self.db.get_graph_edges("00", 2))
