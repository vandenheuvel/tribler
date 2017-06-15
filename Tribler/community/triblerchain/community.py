from binascii import hexlify

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall

from Tribler.Core.simpledefs import NTFY_TUNNEL, NTFY_REMOVE
from Tribler.community.triblerchain.block import TriblerChainBlock
from Tribler.community.triblerchain.database import TriblerChainDB
from Tribler.community.trustchain.community import TrustChainCommunity
from Tribler.dispersy.util import blocking_call_on_reactor_thread

MIN_TRANSACTION_SIZE = 1024*1024


class PendingBytes(object):
    def __init__(self, up, down, clean=None):
        super(PendingBytes, self).__init__()
        self.up = up
        self.down = down
        self.clean = clean

    def add(self, up, down):
        if self.up + up >= 0 and self.down + down >= 0:
            self.up = max(0, self.up + up)
            self.down = max(0, self.down + down)
            if self.clean is not None:
                self.clean.reset(2 * 60)
            return True
        else:
            return False


class TriblerChainCommunity(TrustChainCommunity):
    """
    Community for reputation based on TrustChain tamper proof interaction history.
    """
    BLOCK_CLASS = TriblerChainBlock
    DB_CLASS = TriblerChainDB
    SIGN_DELAY = 5

    def __init__(self, *args, **kwargs):
        super(TriblerChainCommunity, self).__init__(*args, **kwargs)
        self.notifier = None

        # We store the bytes send and received in the tunnel community in a dictionary.
        # The key is the public key of the peer being interacted with, the value a tuple of the up and down bytes
        # This data is not used to create outgoing requests, but _only_ to verify incoming requests
        self.pending_bytes = dict()

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Sun Apr 23 10:06:29 2017
        # curve: None
        # len: 571 bits ~ 144 bytes signature
        # pub: 170 3081a7301006072a8648ce3d020106052b8104002703819200040503dac58c19267f12cb0cf667e480816cd2574acae5293b5
        # 9d7c3da32e02b4747f7e2e9e9c880d2e5e2ba8b7fcc9892cb39b797ef98483ffd58739ed20990f8e3df7d1ec5a7ad2c0338dc206c4383a
        # 943e3e2c682ac4b585880929a947ffd50057b575fc30ec88eada3ce6484e5e4d6fdf41984cd1e51aaacc5f9a51bcc8393aea1f786fc47c
        # bf994cb1339f706df4a
        # pub-sha1 b78a5e252bf2f7be8716c383734f325b9aaff844
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQFA9rFjBkmfxLLDPZn5ICBbNJXSsrl
        # KTtZ18PaMuArR0f34unpyIDS5eK6i3/MmJLLObeX75hIP/1Yc57SCZD44999HsWn
        # rSwDONwgbEODqUPj4saCrEtYWICSmpR//VAFe1dfww7Ijq2jzmSE5eTW/fQZhM0e
        # UaqsxfmlG8yDk66h94b8R8v5lMsTOfcG30o=
        # -----END PUBLIC KEY-----
        master_key = "3081a7301006072a8648ce3d020106052b8104002703819200040503dac58c19267f12cb0cf667e480816cd2574acae" \
                     "5293b59d7c3da32e02b4747f7e2e9e9c880d2e5e2ba8b7fcc9892cb39b797ef98483ffd58739ed20990f8e3df7d1ec5" \
                     "a7ad2c0338dc206c4383a943e3e2c682ac4b585880929a947ffd50057b575fc30ec88eada3ce6484e5e4d6fdf41984c" \
                     "d1e51aaacc5f9a51bcc8393aea1f786fc47cbf994cb1339f706df4a"
        return [dispersy.get_member(public_key=master_key.decode("HEX"))]

    def initialize(self, tribler_session=None):
        super(TriblerChainCommunity, self).initialize()
        if tribler_session:
            self.notifier = tribler_session.notifier
            self.notifier.add_observer(self.on_tunnel_remove, NTFY_TUNNEL, [NTFY_REMOVE])

    def should_sign(self, block):
        """
        Return whether we should sign the passed block.
        @param block: the block that we should sign or not.
        """
        pend = self.pending_bytes.get(block.public_key)
        if not pend or not (pend.up - block.transaction['down'] >= 0 and pend.down - block.transaction['up'] >= 0):
            self.logger.info("Request block counter party does not have enough bytes pending.")
            return False
        return True

    @blocking_call_on_reactor_thread
    def get_statistics(self, public_key=None):
        """
        Returns a dictionary with some statistics regarding the local trustchain database
        :returns a dictionary with statistics
        """
        if public_key is None:
            public_key = self.my_member.public_key
        latest_block = self.persistence.get_latest(public_key)
        statistics = dict()
        statistics["id"] = public_key.encode("hex")
        interacts = self.persistence.get_num_unique_interactors(public_key)
        statistics["peers_that_pk_helped"] = interacts[0] if interacts[0] is not None else 0
        statistics["peers_that_helped_pk"] = interacts[1] if interacts[1] is not None else 0
        if latest_block:
            statistics["total_blocks"] = latest_block.sequence_number
            statistics["total_up"] = latest_block.transaction["total_up"]
            statistics["total_down"] = latest_block.transaction["total_down"]
            statistics["latest_block"] = dict(latest_block)

            # Set up/down
            statistics["latest_block"]["up"] = latest_block.transaction["up"]
            statistics["latest_block"]["down"] = latest_block.transaction["down"]
        else:
            statistics["total_blocks"] = 0
            statistics["total_up"] = 0
            statistics["total_down"] = 0
        return statistics

    @blocking_call_on_reactor_thread
    def on_tunnel_remove(self, subject, change_type, tunnel, candidate):
        """
        Handler for the remove event of a tunnel. This function will attempt to create a block for the amounts that
        were transferred using the tunnel.
        :param subject: Category of the notifier event
        :param change_type: Type of the notifier event
        :param tunnel: The tunnel that was removed (closed)
        :param candidate: The dispersy candidate with whom this node has interacted in the tunnel
        """
        from Tribler.community.tunnel.tunnel_community import Circuit, RelayRoute, TunnelExitSocket
        assert isinstance(tunnel, Circuit) or isinstance(tunnel, RelayRoute) or isinstance(tunnel, TunnelExitSocket), \
            "on_tunnel_remove() was called with an object that is not a Circuit, RelayRoute or TunnelExitSocket"
        assert isinstance(tunnel.bytes_up, int) and isinstance(tunnel.bytes_down, int),\
            "tunnel instance must provide byte counts in int"

        up = tunnel.bytes_up
        down = tunnel.bytes_down
        pk = candidate.get_member().public_key

        # If the transaction is not big enough we discard the bytes up and down.
        if up + down >= MIN_TRANSACTION_SIZE:
            # Tie breaker to prevent both parties from requesting
            if up > down or (up == down and self.my_member.public_key > pk):
                self.register_task("sign_%s" % tunnel.circuit_id,
                                   reactor.callLater(self.SIGN_DELAY, self.sign_block, candidate, pk,
                                                     {'up': tunnel.bytes_up, 'down': tunnel.bytes_down}))
            else:
                pend = self.pending_bytes.get(pk)
                if not pend:
                    task = self.register_task("cleanup_pending_%s" % tunnel.circuit_id,
                                              reactor.callLater(2 * 60, self.cleanup_pending, pk))
                    self.pending_bytes[pk] = PendingBytes(up, down, task)
                else:
                    pend.add(up, down)

    def cleanup_pending(self, public_key):
        self.pending_bytes.pop(public_key, None)

    @inlineCallbacks
    def unload_community(self):
        if self.notifier:
            self.notifier.remove_observer(self.on_tunnel_remove)
        for pk in self.pending_bytes:
            if self.pending_bytes[pk].clean is not None:
                self.pending_bytes[pk].clean.reset(0)
        yield super(TriblerChainCommunity, self).unload_community()

    def get_node(self, public_key, nodes, total_up=None, total_down=None):
        """
        Get a node in an encoded format and with the maximum values given the current dictionary of nodes.

        The format is described as follows:
            {"public_key": public_key, "total_up": total_up, "total_down": total_down}
        This function checks whether the given total up and downloaded amounts are higher than the current recorded (if
        any). Moreover, if the public key does not exist in the nodes list and no total_up and total_down is given, new
        data is retrieved from the database.

        :param public_key: the public key for which a nde dictionary has to be created
        :param nodes: the dictionary of currently recorded nodes
        :param total_up: the total up amount
        :param total_down: the total down amount
        :return: a dictionary corresponding to the node in the correct format
        """
        if public_key in nodes:
            return {"public_key": public_key, "total_up": max(total_up, nodes[public_key]["total_up"]),
                    "total_down": max(total_down, nodes[public_key]["total_down"])}
        else:
            if total_up and total_down:
                return {"public_key": public_key, "total_up": total_up, "total_down": total_down}
            else:
                total_traffic = self.persistence.total_traffic(public_key)
                return {"public_key": public_key, "total_up": total_traffic[0], "total_down": total_traffic[1]}

    @staticmethod
    def update_edges(from_pk, to_pk, edges, amount=0):
        """
        Update the given edge dictionary with the newly acquired data.

        If there is not yet an entry for the public key pair, it is automatically added to the edges dictionary. If
        an edge is already recorded, the given amount is added to the total.

        :param from_pk: the public key of the node where the edge originates from
        :param to_pk: the public key of the node where the edge arrives
        :param edges: the dictionary of edges
        :param amount: the amount of data transferred over this edge
        """
        if from_pk in edges:
            edges[from_pk][to_pk] = edges[from_pk][to_pk] + amount if to_pk in edges[from_pk] else amount
        else:
            edges[from_pk] = {to_pk: amount}

    @blocking_call_on_reactor_thread
    def get_graph(self, public_key=None, neighbor_level=1):
        """
        Return a dictionary with the neighboring nodes and edges of a certain focus node within a certain radius,
        regarding the local MultiChain database.

        :param public_key: the public key of the focus node in raw format
        :param neighbor_level: the radius within which the neighbors have to be returned
        :return: a tuple of a list with nodes and a list with edges
        """
        if public_key is None:
            public_key = hexlify(self.my_member.public_key)

        nodes = {public_key: self.get_node(public_key, {})}
        edges = {}

        for edge in self.persistence.get_graph_edges(public_key, neighbor_level):
            from_pk = str(edge[0])
            to_pk = str(edge[1])
            amount_up = edge[2]
            amount_down = edge[3]
            nodes[from_pk] = self.get_node(from_pk, nodes, total_up=edge[4], total_down=edge[5])
            nodes[to_pk] = self.get_node(to_pk, nodes)
            self.update_edges(from_pk, to_pk, edges, amount=amount_up)
            self.update_edges(to_pk, from_pk, edges, amount=amount_down)

        return_nodes = nodes.values()
        return_edges = []
        for from_pk, edge_list in edges.iteritems():
            new_edges = [{"from": from_pk, "to": to_pk, "amount": amount} for to_pk, amount in edge_list.iteritems()]
            return_edges += new_edges

        return return_nodes, return_edges


class TriblerChainCommunityCrawler(TriblerChainCommunity):
    """
    Extended TriblerChainCommunity that also crawls other TriblerChainCommunities.
    It requests the chains of other TrustChains.
    """

    # Time the crawler waits between crawling a new candidate.
    CrawlerDelay = 5.0

    def on_introduction_response(self, messages):
        super(TriblerChainCommunityCrawler, self).on_introduction_response(messages)
        for message in messages:
            self.send_crawl_request(message.candidate, message.candidate.get_member().public_key)

    def start_walking(self):
        self.register_task("take step", LoopingCall(self.take_step)).start(self.CrawlerDelay, now=False)
