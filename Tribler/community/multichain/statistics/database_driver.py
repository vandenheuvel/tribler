"""
This file contains the functions to get the data from the database.
"""
from sqlite3 import connect

from Tribler.community.multichain.statistics.database_queries import link_to_neighbor_query, link_from_neighbor_query,\
    total_self_up_query, total_other_down_query, total_self_down_query, total_other_up_query, \
    create_table_query, insert_data_query

default_database = ":memory:"


class DatabaseDriver(object):
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

    def total_up(self, focus_pk):
        """
        Gets the total uploaded value from the focus.

        :param focus_pk: primary key of the focus node
        :return: number representing the amount of uploaded data
        """
        total = 0
        self.cursor.execute(total_self_up_query, (focus_pk,))
        value = self.cursor.fetchone()[0]
        if value is not None:
            total += value
        self.cursor.execute(total_other_down_query, (focus_pk,))
        value = self.cursor.fetchone()[0]
        if value is not None:
            total += value
        return total

    def total_down(self, focus_pk):
        """
        Gets the total downloaded value from the focus.

        :param focus_pk: primary key of the focus node
        :return: number representing the amount of downloaded data
        """
        total = 0
        self.cursor.execute(total_self_down_query, (focus_pk,))
        value = self.cursor.fetchone()[0]
        if value is not None:
            total += value
        self.cursor.execute(total_other_up_query, (focus_pk,))
        value = self.cursor.fetchone()[0]
        if value is not None:
            total += value
        return total

    def neighbor_list(self, focus_pk):
        """
        Return a dictionary containing information about all neighbors of the focus node.
        
        For each neighbor, the dictionary contains a key equal to the primary key of the neighbor.
        The value stored under that key is a dictionary containing how much data has been uploaded
        and downloaded to and from that neighbor.

        :param focus_pk: primary key of the focus
        :return: dictionary with for each neighbor of the focus a key, value entry: primary key neighbor, dictionary
        containing the amount of data uploaded and downloaded from that neighbor
        """
        neighbors = {}
        for row in self.cursor.execute(link_to_neighbor_query, (focus_pk,)):
            up = row[1] if row[1] is not None else 0
            down = row[2] if row[2] is not None else 0
            neighbors[row[0]] = {"up": up, "down": down}
        
        for row in self.cursor.execute(link_from_neighbor_query, (focus_pk,)):
            up = row[1] if row[1] is not None else 0
            down = row[2] if row[2] is not None else 0
            if row[0] in neighbors:
                neighbors[row[0]]["up"] += up
                neighbors[row[0]]["down"] += down
            else:
                neighbors[row[0]] = {"up": up, "down": down}

        return neighbors
