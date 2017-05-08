import sqlite3

database_location = "Database/multichain.db"

list_neighbor_query = """
        SELECT DISTINCT hex(public_key_responder) FROM multi_chain where hex(public_key_requester) = ?
        UNION
        SELECT DISTINCT hex(public_key_requester) FROM multi_chain where hex(public_key_responder) = ?
        """

total_up_query = "SELECT sum(up) FROM multi_chain where hex(public_key_requester) = ?"

total_down_query = "SELECT sum(down) FROM multi_chain where hex(public_key_requester) = ?"

neighbor_up_query = "SELECT sum(up) FROM multi_chain WHERE hex(public_key_requester) = ? AND hex(public_key_responder) = ?"

neighbor_down_query = "SELECT sum(down) FROM multi_chain WHERE hex(public_key_requester) = ? AND hex(public_key_responder) = ?"

init_random_focus_query = "SELECT hex(public_key_requester) FROM multi_chain"


class DbDriver(object):
    def __init__(self, database=database_location):
        self.connection = sqlite3.connect(database_location)
        self.cursor = self.connection.cursor()

    def neighbor_list(self, focus_node):
        """
        Return a list of keys for all neighbors of the focus
        :param focus_node: networkNode of the focus
        :return: See description
        """
        ret = []
        for key in self.cursor.execute(list_neighbor_query, (focus_node.public_key, focus_node.public_key)):
            ret.append(key[0])
        return ret

    def total_up(self, focus_node):
        """
        Gets the total uploaded value from the focus
        :param focus_node: networkNode of the focus
        :return: Num representing the amount of uploaded data
        """
        self.cursor.execute(total_up_query, (focus_node.public_key,))
        return self.cursor.fetchone()

    def total_down(self, focus_node):
        """
        Gets the total downloaded value from the focus
        :param focus_node: networkNode of the focus
        :return: Num representing the amount of downloaded data
        """
        self.cursor.execute(total_down_query, (focus_node.public_key,))
        return self.cursor.fetchone()

    def neighbor_up(self, focus_node, neighbor_key):
        """
        Gets the total uploaded from focus_node to neighbor
        :param focus_node: networkNode of the focus
        :param neighbor_key: pulic key of the neighbor's public key
        :return: Num with total upload to neighbor
        """
        self.cursor.execute(neighbor_up_query, (focus_node.public_key, neighbor_key))
        return self.cursor.fetchone()[0]

    def neighbor_down(self, focus_node, neighbor_key):
        """
        Gets the total downloaded from focus_node to neighbor
        :param focus_node: networkNode of the focus
        :param neighbor_key: public key of the neighbor's public key
        :return: Num with total download from neighbor
        """
        self.cursor.execute(neighbor_down_query, (focus_node.public_key, neighbor_key))
        return self.cursor.fetchone()[0]

    def initCurrentFocus(self):
        """
        !!!!    PURELY EXPERIMENTAL    !!!!
        Get the key of a 'random' node in the database
        :return: key of one of the nodes
        """
        self.cursor.execute(init_random_focus_query)
        return self.cursor.fetchone()[0]