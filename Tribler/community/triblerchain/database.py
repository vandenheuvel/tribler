from binascii import hexlify, unhexlify
from random import randint

from sqlite3 import connect
from twisted.internet import task, reactor

from networkx import gnp_random_graph

from Tribler.community.trustchain.database import TrustChainDB
from Tribler.community.trustchain.block import TrustChainBlock

LATEST_TRIBLERCHAIN_AGGREGATES_VERSION = 1

triblerchain_aggregates_schema = u"""
  CREATE TABLE IF NOT EXISTS triblerchain_aggregates(
    public_key_a      TEXT NOT NULL,
    public_key_b      TEXT NOT NULL,
    traffic_a_to_b    INTEGER NOT NULL,
    traffic_b_to_a    INTEGER NOT NULL,
    PRIMARY KEY (public_key_a, public_key_b)
  );
  INSERT INTO option(key, value) VALUES ('aggregate_version', '%s');
  
  CREATE INDEX IF NOT EXISTS idx_public_key_a ON triblerchain_aggregates(public_key_a);
  CREATE INDEX IF NOT EXISTS idx_public_key_b ON triblerchain_aggregates(public_key_b);
""" % LATEST_TRIBLERCHAIN_AGGREGATES_VERSION

upgrade_triblerchain_aggregates_schema = u"""
    DROP TABLE IF EXISTS triblerchain_aggregates;
    DELETE FROM option WHERE key = 'aggregate_version'
"""


class TriblerChainDB(TrustChainDB):
    """
    Persistence layer for the TriblerChain Community.
    """
    LATEST_DB_VERSION = 4

    def __init__(self, working_directory, db_name):
        """
        Create a new connection to the database and add the trust statistics table.
        :param working_directory: directory of the .db file
        :param db_name: name of the db file
        """
        super(TriblerChainDB, self).__init__(working_directory, db_name)
        self.check_statistics_database()
        self.dummy_setup = False

    def add_block(self, block):
        """
        Persist a block and update the total transmission counts in the aggregate table.

        :param block: The data that will be saved.
        """
        super(TriblerChainDB, self).add_block(block)
        self.insert_aggregate_block(block)

    def get_num_unique_interactors(self, public_key):
        """
        Returns the number of people you interacted with (either helped or that have helped you)
        :param public_key: The public key of the member of which we want the information
        :return: A tuple of unique number of interactors that helped you and that you have helped respectively
        """
        peers_you_helped = set()
        peers_helped_you = set()
        for block in self.get_latest_blocks(public_key, limit=-1):
            if int(block.transaction["up"]) > 0:
                peers_you_helped.add(block.link_public_key)
            if int(block.transaction["down"]) > 0:
                peers_helped_you.add(block.link_public_key)
        return len(peers_you_helped), len(peers_helped_you)

    def get_upgrade_script(self, current_version):
        """
        Return the upgrade script for a specific version.
        :param current_version: the version of the script to return.
        """
        if current_version == 2 or current_version == 3:
            return u"""
            DROP TABLE IF EXISTS %s;
            DROP TABLE IF EXISTS option;
            """ % self.db_name

    def insert_aggregate_block(self, block):
        """
        Insert the contents of a TrustChainBlock into the statistics database.

        IMPORTANT: the statistics database uses the hex values of keys, not the raw values.
        :param block: TrustChainBlock to add to the database
        """
        public_key_a = hexlify(block.public_key)
        public_key_b = hexlify(block.link_public_key)
        traffic = block.transaction

        if public_key_a < public_key_b:
            order = (buffer(public_key_a), buffer(public_key_b))
            add_up = traffic["up"]
            add_down = traffic["down"]
        else:
            order = (buffer(public_key_b), buffer(public_key_a))
            add_up = traffic["down"]
            add_down = traffic["up"]

        current_row = self.execute(u"SELECT public_key_a, public_key_b, traffic_a_to_b, traffic_b_to_a "
                                   u"FROM triblerchain_aggregates WHERE public_key_a = ? AND public_key_b = ?",
                                   order).fetchone()

        if current_row:
            # Existing link
            self.execute(u"UPDATE triblerchain_aggregates SET traffic_a_to_b = ?, traffic_b_to_a = ?"
                         u"WHERE public_key_a = ? AND public_key_b = ?",
                         (current_row[2] + add_up, current_row[3] + add_down) + order)
            self.commit()
        else:
            # New link
            self.execute(u"INSERT INTO triblerchain_aggregates(public_key_a, public_key_b, "
                         u"                                    traffic_a_to_b, traffic_b_to_a) "
                         u"VALUES (?, ?, ?, ?)", order + (add_up, add_down))
            self.commit()

    def total_traffic(self, public_key):
        """
        Find the amount of data the public key uploaded and downloaded.
        :param public_key: hex value of the public key
        :return: amount uploaded, amount downloaded
        """
        query = u"""
            SELECT sum(uploaded), sum(downloaded), count(*) FROM (
              SELECT traffic_a_to_b AS uploaded, traffic_b_to_a AS downloaded 
              FROM triblerchain_aggregates WHERE public_key_a = ?
              UNION 
              SELECT traffic_b_to_a as uploaded, traffic_a_to_b AS downloaded 
              FROM triblerchain_aggregates WHERE public_key_b = ?
            )
        """

        result = self.execute(query, (buffer(public_key), buffer(public_key))).fetchone()
        return result[0] or 0, result[1] or 0, result[2] or 0

    def get_graph_edges(self, public_key, neighbor_level=1):
        """
        Gets all the edges for the network graph from the database.
        :param public_key: hex value of the public key of the focus node
        :param neighbor_level: the radius within which the neighbors have to be returned
        :return: a deferred object that will eventually trigger with the query result
        """
        query = u"""SELECT public_key_a, public_key_b FROM triblerchain_aggregates
                    WHERE public_key_a = ? OR public_key_b = ?"""

        for level in range(1, neighbor_level):
            # Add next level neighbors iteratively
            query = u"""
                SELECT DISTINCT ta.public_key_a, ta.public_key_b FROM triblerchain_aggregates ta,
                (%(last_level)s) level%(level)d
                WHERE level%(level)d.public_key_a = ta.public_key_a
                OR level%(level)d.public_key_a = ta.public_key_b
                OR level%(level)d.public_key_b = ta.public_key_a
                OR level%(level)d.public_key_b = ta.public_key_b
            """ % {"level": level, "last_level": query}

        total_traffic = u"""
            SELECT pk, sum(uploaded) AS uploaded, sum(downloaded) AS downloaded, count(*) AS neighbors FROM (
              SELECT public_key_a AS pk, traffic_a_to_b AS uploaded, traffic_b_to_a AS downloaded 
              FROM triblerchain_aggregates
              UNION 
              SELECT public_key_b AS pk, traffic_b_to_a as uploaded, traffic_a_to_b AS downloaded 
              FROM triblerchain_aggregates
            ) GROUP BY pk
        """
        query = u"""
            SELECT ta.public_key_a, ta.public_key_b, ta.traffic_a_to_b, ta.traffic_b_to_a,
                   traffic.uploaded, traffic.downloaded, traffic.neighbors
            FROM triblerchain_aggregates ta
            JOIN (%(query)s) other 
              ON ta.public_key_a = other.public_key_a
              AND ta.public_key_b = other.public_key_b
            JOIN (%(traffic)s) traffic 
              ON ta.public_key_a = traffic.pk
            ORDER BY (ta.traffic_a_to_b + ta.traffic_b_to_a) DESC
        """ % {"query": query, "traffic": total_traffic}

        def get_rows(result):
            return result.fetchall()

        d = task.deferLater(reactor, 0.0, self.execute, query, (buffer(public_key), buffer(public_key)))
        d.addCallback(get_rows)
        return d

    def check_statistics_database(self):
        """
        Create the database if it exists, upgrade it if the version is not the newest one.
        """
        aggregate_version = self.execute(u"SELECT value FROM option WHERE key = 'aggregate_version'").fetchone()
        if aggregate_version:
            if aggregate_version[0].isdigit() and int(aggregate_version[0]) < LATEST_TRIBLERCHAIN_AGGREGATES_VERSION:
                self.executescript(upgrade_triblerchain_aggregates_schema)
                self.executescript(triblerchain_aggregates_schema)
                self.commit()
        else:
            self.executescript(triblerchain_aggregates_schema)
            self.commit()

    #TODO: needs to be removed before merge to Tribler
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
        self.check_statistics_database()

        if use_random:
            blocks = [["00" if edge[0] == 0 else "{0:08x}".format(edge[0] * 41903747),
                       "00" if edge[1] == 0 else "{0:08x}".format(edge[1] * 41903747),
                       randint(100, 1e10), randint(100, 1e10)]
                      for edge in gnp_random_graph(100, 0.05).edges()]

        else:
            blocks = [
                # from, to, up, down
                ['00', '01', 1, 1],
                ['01', '02', 100, 100],
                ['01', '03', 100, 100],
                ['01', '04', 100, 100],
                ['01', '05', 100, 100],
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
            insert_block = TrustChainBlock()
            insert_block.public_key = unhexlify(block[0])
            insert_block.link_public_key = unhexlify(block[1])
            insert_block.transaction = {"up": block[2], "down": block[3]}
            self.insert_aggregate_block(insert_block)
