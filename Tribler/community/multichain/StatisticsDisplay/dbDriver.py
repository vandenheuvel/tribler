"""
This file contains the functions to get the data from the database.
"""
import sqlite3

from Tribler.community.multichain.StatisticsDisplay.databaseQueries import DatabaseQueries

default_database = ":memory:"

class DbDriver(object):
    """
    Driver to get statistics from the database.
    """

    def __init__(self, database=default_database):
        """
        Setup the driver by creating a connection and a cursor.
        If no input argument is given for the databse location, a new database is created
        in memory containing dummy data.

        :param database: Location of the database, memory if none is given.
        """
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        if database == default_database:
            self.cursor.execute(DatabaseQueries.create_table_query)
            self.cursor.execute(DatabaseQueries.insert_data_query)
            self.connection.commit()

    def neighbor_list(self, focus_node):
        """
        Return a list of keys for all neighbors of the focus.

        :param focus_node: networkNode of the focus.
        :return: See description.
        """
        ret = []
        for key in self.cursor.execute(DatabaseQueries.list_neighbor_query,
                                       (focus_node.public_key, focus_node.public_key)):
            ret.append(key[0])
        return ret

    def total_up(self, focus_node):
        """
        Gets the total uploaded value from the focus.

        :param focus_node: networkNode of the focus.
        :return: Num representing the amount of uploaded data.
        """
        total = 0
        self.cursor.execute(DatabaseQueries.total_self_up_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(DatabaseQueries.total_other_down_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def total_down(self, focus_node):
        """
        Gets the total downloaded value from the focus.

        :param focus_node: networkNode of the focus.
        :return: Num representing the amount of downloaded data.
        """
        total = 0
        self.cursor.execute(DatabaseQueries.total_self_down_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(DatabaseQueries.total_other_up_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def neighbor_up(self, focus_node, neighbor_key):
        """
        Gets the total uploaded from focus_node to neighbor.

        :param focus_node: networkNode of the focus.
        :param neighbor_key: pulic key of the neighbor's public key.
        :return: Num with total upload to neighbor.
        """
        total = 0
        self.cursor.execute(DatabaseQueries.neighbor_self_up_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(DatabaseQueries.neighbor_other_down_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def neighbor_down(self, focus_node, neighbor_key):
        """
        Gets the total downloaded from focus_node to neighbor.

        :param focus_node: networkNode of the focus.
        :param neighbor_key: public key of the neighbor's public key.
        :return: Num with total download from neighbor.
        """
        total = 0
        self.cursor.execute(DatabaseQueries.neighbor_self_down_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(DatabaseQueries.neighbor_other_up_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total
