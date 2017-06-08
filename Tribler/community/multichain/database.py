"""
This file contains everything related to persistence for MultiChain.
"""
from binascii import unhexlify
from os import path
from random import randint

from sqlite3 import connect
from networkx import random_regular_graph

from Tribler.community.multichain.block import MultiChainBlock
from Tribler.dispersy.database import Database

DATABASE_DIRECTORY = path.join(u"sqlite")
# Path to the database location + dispersy._workingdirectory
DATABASE_PATH = path.join(DATABASE_DIRECTORY, u"multichain.db")
# Version to keep track if the db schema needs to be updated.
LATEST_DB_VERSION = 3

# Script to creat indexes
create_index_script = u"""
CREATE INDEX IF NOT EXISTS idx_mc_public_key ON multi_chain(public_key);
CREATE INDEX IF NOT EXISTS idx_mc_link_public_key ON multi_chain(link_public_key);
"""

# Schema for the MultiChain DB.
schema = u"""
CREATE TABLE IF NOT EXISTS multi_chain(
 up                   INTEGER NOT NULL,
 down                 INTEGER NOT NULL,
 total_up             UNSIGNED BIG INT NOT NULL,
 total_down           UNSIGNED BIG INT NOT NULL,
 public_key           TEXT NOT NULL,
 sequence_number      INTEGER NOT NULL,
 link_public_key      TEXT NOT NULL,
 link_sequence_number INTEGER NOT NULL,
 previous_hash	      TEXT NOT NULL,
 signature		      TEXT NOT NULL,

 insert_time          TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
 block_hash	          TEXT NOT NULL,

 PRIMARY KEY (public_key, sequence_number)
 );

CREATE TABLE option(key TEXT PRIMARY KEY, value BLOB);
INSERT INTO option(key, value) VALUES('database_version', '""" + str(LATEST_DB_VERSION) + u"""');
""" + create_index_script

upgrade_to_version_2_script = u"""
DROP TABLE IF EXISTS multi_chain;
DROP TABLE IF EXISTS option;
"""

_columns = u"up, down, total_up, total_down, public_key, sequence_number, link_public_key, link_sequence_number, " \
           u"previous_hash, signature, insert_time"
_header = u"SELECT " + _columns + u" FROM multi_chain "


class MultiChainDB(Database):
    """
    Persistence layer for the MultiChain Community.
    Connection layer to SQLiteDB.
    Ensures a proper DB schema on startup.
    """

    def __init__(self, working_directory):
        """
        Sets up the persistence layer ready for use.
        :param working_directory: Path to the working directory
        that will contain the the db at working directory/DATABASE_PATH
        :return:
        """
        super(MultiChainDB, self).__init__(path.join(working_directory, DATABASE_PATH))
        self.open()
        self.dummy_setup = False
        self.executescript(create_index_script)

    def add_block(self, block):
        """
        Persist a block
        :param block: The data that will be saved.
        """
        self.execute(
            u"INSERT INTO multi_chain (up, down, total_up, total_down, public_key, sequence_number, link_public_key,"
            u"link_sequence_number, previous_hash, signature, block_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            block.pack_db_insert())
        self.commit()

    def _get(self, query, params):
        db_result = self.execute(_header + query, params).fetchone()
        return MultiChainBlock(db_result) if db_result else None

    def _getall(self, query, params):
        db_result = self.execute(_header + query, params).fetchall()
        return [MultiChainBlock(db_item) for db_item in db_result]

    def get(self, public_key, sequence_number):
        """
        Get a specific block for a given public key
        :param public_key: The public_key for which the block has to be found.
        :param sequence_number: The specific block to get
        :return: the block or None if it is not known
        """
        return self._get(u"WHERE public_key = ? AND sequence_number = ?", (buffer(public_key), sequence_number))

    def contains(self, block):
        """
        Check if a block is existent in the persistence layer.
        :param block: the block to check
        :return: True if the block exists, else false.
        """
        return self.get(block.public_key, block.sequence_number) is not None

    def get_latest(self, public_key):
        """
        Get the latest block for a given public key
        :param public_key: The public_key for which the latest block has to be found.
        :return: the latest block or None if it is not known
        """
        return self._get(u"WHERE public_key = ? AND sequence_number = (SELECT MAX(sequence_number) FROM multi_chain "
                         u"WHERE public_key = ?)", (buffer(public_key), buffer(public_key)))

    def get_latest_blocks(self, public_key, limit=25):
        return self._getall(u"WHERE public_key = ? ORDER BY sequence_number DESC LIMIT ?", (buffer(public_key), limit))

    def get_block_after(self, block):
        """
        Returns database block with the lowest sequence number higher than the block's sequence_number
        :param block: The block who's successor we want to find
        :return A block
        """
        return self._get(u"WHERE sequence_number > ? AND public_key = ? ORDER BY sequence_number ASC",
                         (block.sequence_number, buffer(block.public_key)))

    def get_block_before(self, block):
        """
        Returns database block with the highest sequence number lower than the block's sequence_number
        :param block: The block who's predecessor we want to find
        :return A block
        """
        return self._get(u"WHERE sequence_number < ? AND public_key = ? ORDER BY sequence_number DESC",
                         (block.sequence_number, buffer(block.public_key)))

    def get_linked(self, block):
        """
        Get the block that is linked to the given block
        :param block: The block for which to get the linked block
        :return: the latest block or None if it is not known
        """
        return self._get(u"WHERE public_key = ? AND sequence_number = ? OR link_public_key = ? AND "
                         u"link_sequence_number = ?", (buffer(block.link_public_key), block.link_sequence_number,
                                                       buffer(block.public_key), block.sequence_number))

    def crawl(self, public_key, sequence_number, limit=100):
        assert limit <= 100, "Don't fetch too much"
        return self._getall(u"WHERE insert_time >= (SELECT MAX(insert_time) FROM multi_chain WHERE public_key = ? AND "
                            u"sequence_number <= ?) AND (public_key = ? OR link_public_key = ?) "
                            u"ORDER BY insert_time ASC LIMIT ?",
                            (buffer(public_key), sequence_number, buffer(public_key), buffer(public_key), limit))

    def get_num_unique_interactors(self, public_key):
        """
        Returns the number of people you interacted with (either helped or that have helped you)
        :param public_key: The public key of the member of which we want the information
        :return: A tuple of unique number of interactors that helped you and that you have helped respectively
        """
        db_query = u"SELECT SUM(CASE WHEN up > 0 THEN 1 ELSE 0 END) AS pk_helped, SUM(CASE WHEN down > 0 THEN 1 ELSE " \
                   u"0 END) AS helped_pk FROM (SELECT link_public_key, SUM(up) AS up, SUM(down) AS down FROM " \
                   u"multi_chain WHERE public_key = ? GROUP BY link_public_key) helpers"
        return self.execute(db_query, (buffer(public_key),)).fetchone()

    def open(self, initial_statements=True, prepare_visioning=True):
        return super(MultiChainDB, self).open(initial_statements, prepare_visioning)

    def close(self, commit=True):
        return super(MultiChainDB, self).close(commit)

    def check_database(self, database_version):
        """
        Ensure the proper schema is used by the database.
        :param database_version: Current version of the database.
        :return:
        """
        assert isinstance(database_version, unicode)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < LATEST_DB_VERSION:
            # Remove all previous data, since we have only been testing so far, and previous blocks might not be
            # reliable. In the future, we should implement an actual upgrade procedure
            self.executescript(upgrade_to_version_2_script)
            self.executescript(schema)
            self.commit()

        return LATEST_DB_VERSION

    def total_traffic(self, public_key):
        """
        Gets the total amount of uploaded and downloaded data.
        :param public_key: public key of the focus node
        :return: amount uploaded, amount downloaded
        """
        query = u"SELECT sum(uploaded), sum(downloaded) FROM (" \
                u"SELECT public_key, sequence_number, up AS uploaded, down AS downloaded " \
                u"FROM multi_chain WHERE public_key = ? " \
                u"UNION " \
                u"SELECT link_public_key, link_sequence_number, down AS uploaded, up AS downloaded " \
                u"FROM multi_chain WHERE link_public_key = ?)"

        result = self.execute(query, (buffer(public_key), buffer(public_key))).fetchone()
        return result[0] or 0, result[1] or 0

    def get_graph_edges(self, public_key, neighbor_level=1):
        """
        Get all edges for the graph focused on the given public key with the given neighbor level as depth.

        The data will have the following format:
        [(from_pk, to_pk, amount_up, amount_down, total_up, total_down), ...]

        Please note that the total_up and total_down are from the node corresponding to the from_pk information. These
        values might not be the most recent one, as it is taken from a block which might not be the most recent one
        available in the database. To get the maximum total_up and total_down, make sure to take the maximum for a given
        node over different rows.

        :param public_key: the public key of which the neighbors have to be retrieved
        :param neighbor_level: the depth of the resulting graph
        :return: a list with tuples as described above
        """
        # Select the first layer of neighbors.
        query = u"""SELECT DISTINCT public_key, link_public_key FROM multi_chain
                WHERE link_public_key = ? OR public_key = ?"""

        # Recursively query the higher order neighbors (i.e. neighbors further away from the public_key).
        for level in range(1, neighbor_level):
            query = u"""SELECT DISTINCT mc.public_key, mc.link_public_key FROM multi_chain mc,
                    (%(last_level)s) level%(level)d
                    WHERE level%(level)d.public_key = mc.public_key
                    OR level%(level)d.public_key = mc.link_public_key
                    OR level%(level)d.link_public_key = mc.public_key
                    OR level%(level)d.link_public_key = mc.link_public_key
                    """ % {"level": level, "last_level": query}

        # Retrieve the edges for the correct node pairs.
        query = u"""SELECT mc.public_key, mc.link_public_key, sum(up), sum(down), mc.total_up, mc.total_down
                FROM multi_chain mc, (%(query)s) other
                WHERE mc.public_key = other.public_key AND mc.link_public_key = other.link_public_key
                GROUP BY mc.public_key, mc.link_public_key""" % {"query": query}

        # Execute the query.
        return self.execute(query, (buffer(public_key), buffer(public_key))).fetchall()

    def use_dummy_data(self, use_random=True):
        """
        Creates a new database and fills it with dummy data.
        :param use_random: true if you want randomly generated data
        """
        if self.dummy_setup:
            return

        self.dummy_setup = True

        self.close()

        self._connection = connect(":memory:")
        self._cursor = self._connection.cursor()

        self.check_database(u"0")
        seq_num = 0

        if use_random:
            blocks = [[str(edge[0]) if len(str(edge[0])) > 1 else "0" + str(edge[0]),
                       str(edge[1]) if len(str(edge[1])) > 1 else "0" + str(edge[1]),
                       randint(101, 200), randint(121, 200)]
                      for edge in random_regular_graph(4, 26).edges()]
        else:
            blocks = [
                # from, to, up, down
                ['00', '01', 10, 5],
                ['01', '00', 3, 6],
                ['01', '00', 46, 12],
                ['00', '02', 123, 6],
                ['02', '00', 21, 3],
                ['00', '03', 22, 68],
                ['03', '00', 234, 12],
                ['00', '04', 57, 357],
                ['04', '00', 223, 2],
                ['01', '05', 13, 5],
                ['05', '01', 14, 6],
                ['01', '06', 234, 5],
                ['01', '10', 102, 5],
                ['10', '01', 123, 0],
                ['02', '07', 87, 5],
                ['07', '02', 342, 1],
                ['02', '08', 0, 5],
                ['02', '08', 78, 23],
                ['03', '04', 20, 5],
                ['04', '03', 3, 5],
                ['04', '09', 650, 5],
                ['09', '04', 650, 5],
                ['05', '06', 234, 5],
                ['06', '05', 5, 323],
                ['06', '07', 12, 5],
                ['07', '06', 12, 5],
                ['09', '10', 51, 123],
                ['10', '09', 76, 5]
            ]

        for block in blocks:
            total_up_0, total_down_0 = self.total_traffic(block[0])
            total_up_1, total_down_1 = self.total_traffic(block[1])
            self.add_block(MultiChainBlock([block[2], block[3], total_up_0 + block[2],
                                            total_down_0 + block[3], unhexlify(block[0]), seq_num,
                                            unhexlify(block[1]), seq_num + 1, '', '', None]))
            self.add_block(MultiChainBlock([block[3], block[2], total_up_1 + block[3],
                                            total_down_1 + block[2], unhexlify(block[1]), seq_num + 1,
                                            unhexlify(block[0]), seq_num, '', '', None]))
            seq_num += 2
