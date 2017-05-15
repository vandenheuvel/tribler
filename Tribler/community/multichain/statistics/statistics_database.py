

from Tribler.community.multichain.database import MultiChainDB


class StatisticsDB(MultiChainDB):
    """
    Statistics connection for the trust chain database.
    """

    def __init__(self, working_directory):
        super(StatisticsDB, self).__init__(working_directory)

    def total_up(self, public_key):
        """
        Gets the total uploaded value from the focus.

        :param public_key: public key of the focus node
        :return: number representing the amount of uploaded data
        """
        block = self.get_latest(public_key)
        return block.total_up

    def total_down(self, public_key):
        """
        Gets the total downloaded value from the focus.

        :param public_key: public key of the focus node
        :return: number representing the amount of uploaded data
        """
        block = self.get_latest(public_key)
        return block.total_down

    def neighbor_list(self, public_key):
        """
        Return a dictionary containing information about all neighbors of the focus node.

        For each neighbor, the dictionary contains a key equal to the primary key of the neighbor.
        The value stored under that key is a dictionary containing how much data has been uploaded
        and downloaded to and from that neighbor.

        :param public_key: primary key of the focus node
        :return: dictionary with for each neighbor of the focus a key, value entry: primary key neighbor, dictionary
        containing the amount of data uploaded and downloaded from that neighbor
        """
        query = u"SELECT link_public_key, sum(up), sum(down) FROM multi_chain " \
                u"WHERE public_key = ? GROUP BY link_public_key"
        neighbors = {}
        for row in self.execute(query, (public_key,)):
            neighbors[row[0]] = {"up": row[1] or 0, "down": row[2] or 0}

        return neighbors