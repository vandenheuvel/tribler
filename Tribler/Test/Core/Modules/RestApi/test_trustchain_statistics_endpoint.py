import json

from twisted.internet.defer import inlineCallbacks

from Tribler.Test.Core.Modules.RestApi.base_api_test import AbstractApiTest
from Tribler.Test.twisted_thread import deferred
from Tribler.community.triblerchain.community import TriblerChainCommunity
from Tribler.dispersy.dispersy import Dispersy
from Tribler.dispersy.endpoint import ManualEnpoint
from Tribler.dispersy.member import DummyMember
from Tribler.dispersy.util import blocking_call_on_reactor_thread


class TestTrustchainStatisticsEndpoint(AbstractApiTest):

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, autoload_discovery=True):
        yield super(TestTrustchainStatisticsEndpoint, self).setUp(autoload_discovery=autoload_discovery)

        self.dispersy = Dispersy(ManualEnpoint(0), self.getStateDir())
        self.dispersy._database.open()
        master_member = DummyMember(self.dispersy, 1, "a" * 20)
        self.member = self.dispersy.get_new_member(u"curve25519")

        self.tribler_chain_community = TriblerChainCommunity(self.dispersy, master_member, self.member)
        self.dispersy.get_communities = lambda: [self.tribler_chain_community]
        self.session.get_dispersy_instance = lambda: self.dispersy
        self.session.config.get_trustchain_enabled = lambda: True

    @deferred(timeout=10)
    def test_get_statistics_no_data(self):
        """
        Testing what the API returns if no trustchain community is present.
        """
        public_key = '30'
        neighbor_level = 0

        def verify_response(response):
            response_json = json.loads(response)

            self.assertIn("focus_node", response_json)
            self.assertEqual(response_json["focus_node"], public_key)
            self.assertIn("neighbor_level", response_json)
            self.assertEqual(response_json["neighbor_level"], neighbor_level)
            self.assertIn("nodes", response_json)
            list_of_nodes = [node["public_key"] for node in response_json["nodes"]]
            self.assertListEqual([public_key], list_of_nodes)
            self.assertIn("edges", response_json)
            list_of_edges = response_json["edges"]
            self.assertListEqual([], list_of_edges)

        self.should_check_equality = False
        request = 'trustchain/network?focus_node=' + public_key +\
                  '&neighbor_level=' + str(neighbor_level) +\
                  '&dataset=static'
        return self.do_request(request, expected_code=200).addCallback(verify_response)
