class NetworkNode(object):
    def __init__(self, public_key, db_driver):
        """
        Creates a networkNode object.

        :param public_key: public key of the public key of the node
        :param db_driver: the database driver to use for querying
        """
        self.public_key = public_key
        self.driver = db_driver
        self.neighbor_keys = self.driver.neighbor_list(self)
        self.total_uploaded = -1
        self.total_downloaded = -1

    def total_up(self):
        if self.total_uploaded < 0:
            self.total_uploaded = self.driver.total_up(self)
        return self.total_uploaded

    def total_down(self):
        if self.total_downloaded < 0:
            self.total_downloaded = self.driver.total_down(self)
        return self.total_downloaded

    def neighbor_up(self, neighbor_key):
        return self.driver.neighbor_up(self, neighbor_key)

    def neighbor_down(self, neighbor_key):
        return self.driver.neighbor_down(self, neighbor_key)

    def neighbor_focus(self, neighbor_index):
        return NetworkNode(self.neighbor_keys[neighbor_index], self.driver)