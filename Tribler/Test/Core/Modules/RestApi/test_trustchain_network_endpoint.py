"""
This module validates the functions defined in the TrustchainNetworkEndpoint Endpoint
"""
from binascii import hexlify
from json import dumps, loads

from twisted.internet.defer import inlineCallbacks
from twisted.web import http

from Tribler.Core.Modules.restapi.trustchain_endpoint import TrustChainNetworkEndpoint
from Tribler.Core.exceptions import OperationNotEnabledByConfigurationException
from Tribler.community.triblerchain.community import TriblerChainCommunity
from Tribler.dispersy.dispersy import Dispersy
from Tribler.dispersy.endpoint import ManualEnpoint
from Tribler.dispersy.member import DummyMember
from Tribler.dispersy.util import blocking_call_on_reactor_thread
from Tribler.Test.Core.Modules.RestApi.base_api_test import AbstractApiTest
from Tribler.Test.Core.base_test import MockObject
from Tribler.Test.twisted_thread import deferred


class TestTrustchainNetworkEndpoint(AbstractApiTest):
    """
    Evaluate the TrustNetworkEndpoint, the endpoint from which you can retrieve
    aggregated data from the trustchain.
    """

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self, autoload_discovery=True):
        yield super(TestTrustchainNetworkEndpoint, self).setUp(autoload_discovery=autoload_discovery)

        self.dispersy = Dispersy(ManualEnpoint(0), self.getStateDir())
        self.dispersy._database.open()
        master_member = DummyMember(self.dispersy, 1, "a" * 20)
        self.member = self.dispersy.get_new_member(u"curve25519")

        self.tribler_chain_community = TriblerChainCommunity(self.dispersy, master_member, self.member)
        self.dispersy.get_communities = lambda: [self.tribler_chain_community]
        self.session.get_dispersy_instance = lambda: self.dispersy

    def set_up_endpoint_request(self, dataset, focus_node, neighbor_level):
        """
        Create a mocked session, create a TrustchainNetworkEndpoint instance
        and create a request from the provided parameters.

        :param dataset: dataset to use for the request
        :param focus_node: node for which to request the data
        :param neighbor_level: amount of levels from this node to request
        :return: a 2-tuple of the TrustchainNetworkEndpoint and the request
        """
        mocked_session = MockObject()
        network_endpoint = TrustChainNetworkEndpoint(mocked_session)
        network_endpoint.get_tribler_chain_community = lambda: self.tribler_chain_community
        request = MockObject()
        request.setHeader = lambda header, flags: None
        request.setResponseCode = lambda status_code: None
        request.args = {"dataset": [str(dataset)], "focus_node": [str(focus_node)],
                        "neighbor_level": [str(neighbor_level)]}
        return network_endpoint, request

    def test_get_no_focus_node(self):
        """
        Evaluate whether the API returns an Bad Request error if there is no focus node specified.
        """
        exp_message = {"error": "focus_node parameter missing"}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", "X", 1)
        del request.args["focus_node"]
        self.assertEqual(dumps(exp_message), network_endpoint.render_GET(request))

    def test_get_empty_focus_node(self):
        """
        Evaluate whether the API returns a Bad Request error if the focus node is empty.
        """
        exp_message = {"error": "focus_node parameter empty"}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", "X", 1)
        request.args["focus_node"] = [""]
        self.assertEqual(dumps(exp_message), network_endpoint.render_GET(request))

    def test_get_no_edges(self):
        """
        Evaluate whether the API passes the correct data if there are no edges returned.
        """
        self.tribler_chain_community.get_graph = lambda public_key, neighbor_level: (
            [{"public_key": "xyz", "total_up": 0, "total_down": 0}], [])
        exp_message = {"user_node": hexlify(self.tribler_chain_community.my_member.public_key),
                       "focus_node": "30",
                       "neighbor_level": 1,
                       "nodes": [{"public_key": "xyz", "total_up": 0, "total_down": 0}],
                       "edges": []}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", 30, 1)
        self.assertEqual(dumps(exp_message), network_endpoint.render_GET(request))

    def test_get_edges(self):
        """
        Evaluate whether the API passes the correct data if there are edges returned.
        """
        self.tribler_chain_community.get_graph = lambda public_key, neighbor_level: (
            [{"public_key": "xyz", "total_up": 0, "total_down": 0}], [
                {"from": "xyz", "to": "abc", "amount": 30}])
        exp_message = {"user_node": hexlify(self.tribler_chain_community.my_member.public_key),
                       "focus_node": "30",
                       "neighbor_level": 1,
                       "nodes": [{"public_key": "xyz", "total_up": 0, "total_down": 0}],
                       "edges": [{"from": "xyz", "to": "abc", "amount": 30}]}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", 30, 1)
        self.assertEqual(dumps(exp_message), network_endpoint.render_GET(request))

    def test_get_self(self):
        """
        Evaluate whether the API uses the own public key when public_key is set to 'self'.
        """
        user_public_key = hexlify(self.member.public_key)
        exp_message = {"user_node": user_public_key,
                       "focus_node": user_public_key,
                       "neighbor_level": 1,
                       "nodes": [{"public_key": user_public_key, "total_up": 0, "total_down": 0}],
                       "edges": []}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", "self", 1)
        self.assertEquals(dumps(exp_message), network_endpoint.render_GET(request))

    def test_negative_neighbor_level(self):
        """
        Evaluate whether the API uses neighbor level 1 when a negative number is provided.
        """
        user_public_key = hexlify(self.member.public_key)
        exp_message = {"user_node": user_public_key,
                       "focus_node": hexlify(self.member.public_key),
                       "neighbor_level": 1,
                       "nodes": [{"public_key": user_public_key, "total_up": 0, "total_down": 0}],
                       "edges": []}
        network_endpoint, request = self.set_up_endpoint_request("trustchain", "self", -1)
        self.assertEquals(dumps(exp_message), network_endpoint.render_GET(request))

    def test_empty_dataset(self):
        """
        Evaluate whether the API sends a response when the dataset is not well-defined.
        """
        user_public_key = hexlify(self.member.public_key)
        exp_message = {"user_node": user_public_key,
                       "focus_node": user_public_key,
                       "neighbor_level": 1,
                       "nodes": [{"public_key": user_public_key, "total_up": 0, "total_down": 0}],
                       "edges": []}
        network_endpoint, request = self.set_up_endpoint_request("", "self", 1)
        self.assertEquals(dumps(exp_message), network_endpoint.render_GET(request))

    def test_no_dataset(self):
        """
        Evaluate whether the API sends a response when the dataset is not defined.
        """
        user_public_key = hexlify(self.member.public_key)
        exp_message = {"nodes": [{"public_key": user_public_key, "total_down": 0, "total_up": 0}],
                       "neighbor_level": 1,
                       "user_node": user_public_key,
                       "focus_node": user_public_key,
                       "edges": []}

        network_endpoint, request = self.set_up_endpoint_request("", "self", 1)
        del request.args["dataset"]
        self.assertEquals(dumps(exp_message), network_endpoint.render_GET(request))

    @blocking_call_on_reactor_thread
    def test_static_dataset(self):
        """
        Evaluate whether the API sends a response when the static dummy dataset is initialized.
        """
        network_endpoint, request = self.set_up_endpoint_request("static", "03", 1)
        response = network_endpoint.render_GET(request)
        self.assertTrue(self.tribler_chain_community.persistence.dummy_setup)
        self.assertEqual(len(loads(response)["nodes"]), 3)

    @blocking_call_on_reactor_thread
    def test_random_dataset(self):
        """
        Evaluate whether the API sends a response when the random dummy dataset is initialized.
        """
        network_endpoint, request = self.set_up_endpoint_request("random", "25", 1)
        response = network_endpoint.render_GET(request)
        self.assertTrue(self.tribler_chain_community.persistence.dummy_setup)
        self.assertEqual(len(loads(response)["nodes"]), 5)

    @blocking_call_on_reactor_thread
    def test_self_dummy_data(self):
        """
        Evaluate whether the API picks "0" as public key when dummy data is used.
        """
        network_endpoint, request = self.set_up_endpoint_request("static", "self", 1)
        response = network_endpoint.render_GET(request)
        self.assertEqual(loads(response)["focus_node"], "00")

        del request.args["dataset"]
        response = network_endpoint.render_GET(request)
        self.assertEqual(loads(response)["focus_node"], "00")

    @deferred(timeout=10)
    def test_mc_community_exception(self):
        """
        Evaluate whether the API returns the correct error when the trustchain community can't be found.
        """
        mocked_session = MockObject()
        network_endpoint = TrustChainNetworkEndpoint(mocked_session)
        network_endpoint.get_tribler_chain_community = lambda:\
            (_ for _ in ()).throw(OperationNotEnabledByConfigurationException("trustchain is not enabled"))

        exp_message = {"error": "trustchain is not enabled"}
        return self.do_request('trustchain/network?focus_node=self',
                               expected_code=http.NOT_FOUND, expected_json=exp_message)

    @deferred(timeout=10)
    def test_mc_community_exception_dummy_data(self):
        """
        Evaluate whether the API returns the correct error when the trustchain community can't be found with dummy data.
        """
        mocked_session = MockObject()
        network_endpoint = TrustChainNetworkEndpoint(mocked_session)
        network_endpoint.get_tribler_chain_community = lambda:\
            (_ for _ in ()).throw(OperationNotEnabledByConfigurationException("trustchain is not enabled"))

        exp_message = {"error": "trustchain is not enabled"}
        return self.do_request('trustchain/network?dataset=static&focus_node=self',
                               expected_code=http.NOT_FOUND, expected_json=exp_message)
