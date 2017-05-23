import datetime
import os
from math import pow
from twisted.internet.defer import inlineCallbacks

from Tribler.Test.Community.Multichain.test_multichain_utilities import TestBlock, MultiChainTestCase
from Tribler.dispersy.util import blocking_call_on_reactor_thread
from Tribler.community.multichain.database import MultiChainDB, DATABASE_DIRECTORY


class TestDatabase(MultiChainTestCase):
    """
    Tests the Database for MultiChain community.
    """

    def __init__(self, *args, **kwargs):
        super(TestDatabase, self).__init__(*args, **kwargs)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, **kwargs):
        yield super(TestDatabase, self).setUp(**kwargs)
        path = os.path.join(self.getStateDir(), DATABASE_DIRECTORY)
        if not os.path.exists(path):
            os.makedirs(path)
        self.db = MultiChainDB(self.getStateDir())
        self.block1 = TestBlock()
        self.block2 = TestBlock()
        self.block3 = TestBlock()

    @blocking_call_on_reactor_thread
    def test_add_block(self):
        # Act
        self.db.add_block(self.block1)
        # Assert
        result = self.db.get_latest(self.block1.public_key)
        self.assertEqual_block(self.block1, result)

    @blocking_call_on_reactor_thread
    def test_get_num_interactors(self):
        """
        Test whether the right number of interactors is returned
        """
        self.block2 = TestBlock(previous=self.block1)
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.assertEqual((2, 2), self.db.get_num_unique_interactors(self.block1.public_key))

    @blocking_call_on_reactor_thread
    def test_add_two_blocks(self):
        # Act
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        # Assert
        result = self.db.get_latest(self.block2.public_key)
        self.assertEqual_block(self.block2, result)

    @blocking_call_on_reactor_thread
    def test_get_block_non_existing(self):
        # Act
        result = self.db.get_latest(self.block1.public_key)
        # Assert
        self.assertEqual(None, result)

    @blocking_call_on_reactor_thread
    def test_contains_block_id_positive(self):
        # Act
        self.db.add_block(self.block1)
        # Assert
        self.assertTrue(self.db.contains(self.block1))

    @blocking_call_on_reactor_thread
    def test_contains_block_id_negative(self):
        # Act & Assert
        self.assertFalse(self.db.contains(self.block1))

    @blocking_call_on_reactor_thread
    def test_get_linked_forward(self):
        # Arrange
        self.block2 = TestBlock.create(self.db, self.block2.public_key, link=self.block1)
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        # Act
        result = self.db.get_linked(self.block1)
        # Assert
        self.assertEqual_block(self.block2, result)

    @blocking_call_on_reactor_thread
    def test_get_linked_backwards(self):
        # Arrange
        self.block2 = TestBlock.create(self.db, self.block2.public_key, link=self.block1)
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        # Act
        result = self.db.get_linked(self.block2)
        # Assert
        self.assertEqual_block(self.block1, result)

    @blocking_call_on_reactor_thread
    def test_get_block_after(self):
        # Arrange
        self.block2.public_key = self.block1.public_key
        self.block2.sequence_number = self.block1.sequence_number + 1
        block3 = TestBlock()
        block3.public_key = self.block2.public_key
        block3.sequence_number = self.block2.sequence_number + 10
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.db.add_block(block3)
        # Act
        result = self.db.get_block_after(self.block2)
        # Assert
        self.assertEqual_block(block3, result)

    @blocking_call_on_reactor_thread
    def test_get_block_before(self):
        # Arrange
        self.block2.public_key = self.block1.public_key
        self.block2.sequence_number = self.block1.sequence_number + 1
        block3 = TestBlock()
        block3.public_key = self.block2.public_key
        block3.sequence_number = self.block2.sequence_number + 10
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.db.add_block(block3)
        # Act
        result = self.db.get_block_before(self.block2)
        # Assert
        self.assertEqual_block(self.block1, result)

    @blocking_call_on_reactor_thread
    def test_save_large_upload_download_block(self):
        """
        Test if the block can save very large numbers.
        """
        # Arrange
        self.block1.total_up = long(pow(2, 62))
        self.block1.total_down = long(pow(2, 62))
        # Act
        self.db.add_block(self.block1)
        # Assert
        result = self.db.get_latest(self.block1.public_key)
        self.assertEqual_block(self.block1, result)

    @blocking_call_on_reactor_thread
    def test_get_insert_time(self):
        # Arrange
        # Upon adding the block to the database, the timestamp will get added.
        self.db.add_block(self.block1)

        # Act
        # Retrieving the block from the database will result in a block with a timestamp
        result = self.db.get_latest(self.block1.public_key)

        insert_time = datetime.datetime.strptime(result.insert_time,
                                                 "%Y-%m-%d %H:%M:%S")

        # We store UTC timestamp
        time_difference = datetime.datetime.utcnow() - insert_time

        # Assert
        self.assertEquals(time_difference.days, 0)
        self.assertLess(time_difference.seconds, 10,
                        "Difference in stored and retrieved time is too large.")

    @blocking_call_on_reactor_thread
    def set_db_version(self, version):
        self.db.executescript(u"UPDATE option SET value = '%d' WHERE key = 'database_version';" % version)
        self.db.close(commit=True)
        self.db = MultiChainDB(self.getStateDir())

    @blocking_call_on_reactor_thread
    def test_database_upgrade(self):
        self.set_db_version(1)
        version, = next(self.db.execute(u"SELECT value FROM option WHERE key = 'database_version' LIMIT 1"))
        self.assertEqual(version, u"3")

    @blocking_call_on_reactor_thread
    def test_database_create(self):
        self.set_db_version(0)
        version, = next(self.db.execute(u"SELECT value FROM option WHERE key = 'database_version' LIMIT 1"))
        self.assertEqual(version, u"3")

    @blocking_call_on_reactor_thread
    def test_database_no_downgrade(self):
        self.set_db_version(200000)
        version, = next(self.db.execute(u"SELECT value FROM option WHERE key = 'database_version' LIMIT 1"))
        self.assertEqual(version, u"200000")

    @blocking_call_on_reactor_thread
    def test_block_to_dictionary(self):
        """
        Test whether a block is correctly represented when converted to a dictionary
        """
        block_dict = dict(self.block1)
        self.assertEqual(block_dict["up"], self.block1.up)
        self.assertEqual(block_dict["down"], self.block1.down)
        self.assertEqual(block_dict["insert_time"], self.block1.insert_time)

    @blocking_call_on_reactor_thread
    def test_total_up(self):
        """
        The database should return the correct amount of uploaded data.
        """
        self.block2.total_up = 0

        self.db.add_block(self.block1)
        self.db.add_block(self.block2)

        self.assertEqual(self.block1.total_up, self.db.total_up(self.block1.public_key))
        self.assertEqual(0, self.db.total_up(self.block2.public_key))
        self.assertEqual(0, self.db.total_up(self.block3.public_key))

    @blocking_call_on_reactor_thread
    def test_total_down(self):
        """
        The database should return the correct amount of downloaded data.
        """
        self.block2.total_down = 0

        self.db.add_block(self.block1)
        self.db.add_block(self.block2)

        self.assertEqual(self.block2.total_down, self.db.total_down(self.block2.public_key))
        self.assertEqual(0, self.db.total_down(self.block2.public_key))
        self.assertEqual(0, self.db.total_down(self.block3.public_key))

    @blocking_call_on_reactor_thread
    def test_neighbors(self):
        """
        The database should return the correct list of neighbors and the traffic to and from them.
        """
        focus_block1 = TestBlock()
        focus_block2 = TestBlock()

        # All blocks have the same public key
        self.block2.public_key = self.block1.public_key
        self.block3.public_key = self.block1.public_key

        self.block1.link_public_key = focus_block1.public_key
        self.block2.link_public_key = focus_block1.public_key
        self.block3.link_public_key = focus_block2.public_key

        # Add all blocks + one redundant block
        self.db.add_block(self.block1)
        self.db.add_block(self.block2)
        self.db.add_block(self.block3)
        self.db.add_block(focus_block1)

        expected_result = {focus_block1.public_key:
                               {"up": self.block1.up + self.block2.up, "down": self.block1.down + self.block2.down},
                           focus_block2.public_key: {"up": self.block3.up, "down": self.block3.down}}

        self.assertDictEqual(expected_result, self.db.neighbor_list(self.block1.public_key))

    @blocking_call_on_reactor_thread
    def test_random_dummy_data(self):
        """
        The database should contain 104 rows when random dummy data is used.
        """
        self.db.use_dummy_data(use_random=True)

        num_rows = self.db.execute(u"SELECT count (*) FROM multi_chain").fetchone()[0]
        self.assertEqual(num_rows, 104)
        self.assertTrue(self.db.dummy_setup)

    @blocking_call_on_reactor_thread
    def test_static_dummy_dta(self):
        """
        The database should contain the fixed dataset when non-random dummy data is used.
        """
        self.db.use_dummy_data(use_random=False)

        num_rows = self.db.execute(u"SELECT count (*) FROM multi_chain").fetchone()[0]
        self.assertEqual(num_rows, 56)
        self.assertTrue(self.db.dummy_setup)

        self.db.use_dummy_data(use_random=True)

        num_rows = self.db.execute(u"SELECT count (*) FROM multi_chain").fetchone()[0]
        self.assertEqual(num_rows, 56)
        self.assertTrue(self.db.dummy_setup)
