"""
This file contains a wrapper object to ease the querying on the database.
"""

class NetworkNode(object):
    """
    The network node object allows for easier querying of the database with respect to a single focus node.
    """
    def __init__(self, public_key, db_driver):
        """
        Creates a network node object.

        :param public_key: public key of the public key of the node.
        :param db_driver: the database driver to use for querying.
        """
        self.public_key = public_key
        self.driver = db_driver
        self.neighbor_keys = self.driver.neighbor_list(self)
        self.total_uploaded = -1
        self.total_downloaded = -1

    def total_up(self):
        """
        Finds the total amount of data uploaded by this node.

        :return: See above.
        """
        if self.total_uploaded < 0:
            self.total_uploaded = self.driver.total_up(self)
        return self.total_uploaded

    def total_down(self):
        """
        Finds the total amount of data downloaded by this node.

        :return: See above.
        """
        if self.total_downloaded < 0:
            self.total_downloaded = self.driver.total_down(self)
        return self.total_downloaded

    def neighbor_up(self, neighbor_key):
        """
        Finds the amount of data this node uploaded to the neighbor with the given key.

        :param neighbor_key: Public key of the neighbor.
        :return: The amount of data uploaded, 0 if the key does not belong to one of the neighbors.
        """
        return self.driver.neighbor_up(self, neighbor_key)

    def neighbor_down(self, neighbor_key):
        """
        Finds the amount of data this node downloaded from the neighbor with the given key.

        :param neighbor_key: Public key of the neighbor.
        :return: The amount of data downloaded, 0 if the key does not belong to one of the neighbors.
        """
        return self.driver.neighbor_down(self, neighbor_key)
