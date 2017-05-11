"""
This file contains the functions to get the data from the database.
"""
from sqlite3 import connect

from Tribler.community.multichain.statistics.database_queries import list_neighbor_query, total_self_up_query, \
    total_other_down_query, total_self_down_query, total_other_up_query, neighbor_self_up_query, \
    neighbor_other_down_query, neighbor_self_down_query, neighbor_other_up_query, create_table_query, insert_data_query

default_database = ":memory:"


class DbDriver(object):
    """
    Driver to get statistics from the database.
    """

    def __init__(self, database=default_database):
        """
        Setup the driver by creating a connection and a cursor.

        If no input argument is given for the database location, a new database is created
        in memory containing dummy data.

        :param database: location of the database, memory if none is given
        """
        self.connection = connect(database)
        self.cursor = self.connection.cursor()
        if database == default_database:
            self.cursor.execute(create_table_query)
            self.cursor.execute(insert_data_query)
            self.connection.commit()

    def neighbor_list(self, focus_node):
        """
        Return a list of keys for all neighbors of the focus.

        :param focus_node: network node of the focus
        :return: see description
        """
        return [neighbor[0] for neighbor in self.cursor.execute(list_neighbor_query,
                                                                (focus_node.public_key, focus_node.public_key))]
        #
        # neighbors = []
        # for key in self.cursor.execute(list_neighbor_query,
        #                                (focus_node.public_key, focus_node.public_key)):
        #     neighbors.append(key[0])
        # return neighbors

    def total_up(self, focus_node):
        """
        Gets the total uploaded value from the focus.

        :param focus_node: networkNode of the focus
        :return: number representing the amount of uploaded data
        """
        total = 0
        self.cursor.execute(total_self_up_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(total_other_down_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def total_down(self, focus_node):
        """
        Gets the total downloaded value from the focus.

        :param focus_node: network node of the focus
        :return: number representing the amount of downloaded data
        """
        total = 0
        self.cursor.execute(total_self_down_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(total_other_up_query, (focus_node.public_key,))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def neighbor_up(self, focus_node, neighbor_key):
        """
        Gets the total uploaded from focus_node to neighbor.

        :param focus_node: network node of the focus
        :param neighbor_key: public key of the neighbor's public key
        :return: number with total upload to neighbor
        """
        total = 0
        self.cursor.execute(neighbor_self_up_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(neighbor_other_down_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total

    def neighbor_down(self, focus_node, neighbor_key):
        """
        Gets the total downloaded from focus_node to neighbor.

        :param focus_node: network node of the focus
        :param neighbor_key: public key of the neighbor's public key
        :return: number with total download from neighbor
        """
        total = 0
        self.cursor.execute(neighbor_self_down_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        self.cursor.execute(neighbor_other_up_query, (focus_node.public_key, neighbor_key))
        val = self.cursor.fetchone()[0]
        if val is not None:
            total += val
        return total
