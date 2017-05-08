import os
from ConfigParser import RawConfigParser

from Tribler.Core.Config.tribler_config import TriblerConfig
import Tribler.Core.Upgrade.config_converter
from Tribler.Test.Core.base_test import TriblerCoreTest


class TestConfigUpgrade70to71(TriblerCoreTest):
    """
    Contains all tests that test the config conversion from 70 to 71.
    """
    from Tribler.Test import Core
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(Core.__file__)), "data/config_files/")

    def test_read_test_tribler_conf(self):
        old_config = RawConfigParser()
        old_config.read(os.path.join(self.CONFIG_PATH, "tribler70.conf"))
        new_config = TriblerConfig()
        result_config = Tribler.Core.Upgrade.config_converter.convert_tribler(new_config, old_config)
        self.assertEqual(result_config.get_default_safeseeding_enabled(), True)

    def test_read_test_libtribler_conf(self):
        old_config = RawConfigParser()
        old_config.read(os.path.join(self.CONFIG_PATH, "libtribler70.conf"))
        new_config = TriblerConfig()
        result_config = Tribler.Core.Upgrade.config_converter.convert_libtribler(new_config, old_config)
        self.assertEqual(result_config.get_permid_keypair_filename(), "/anon/TriblerDir.gif")
        self.assertEqual(result_config.get_tunnel_community_socks5_listen_ports(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(result_config.get_metadata_store_dir(), "/home/.Tribler/testFile")
        self.assertEqual(result_config.get_anon_proxy_settings(), (2, ("127.0.0.1", [5, 4, 3, 2, 1]), 'None'))
        self.assertEqual(result_config.get_credit_mining_sources(),
                         {'boosting_sources': ['source1', 'source2'],
                          'boosting_enabled': ['testenabled'],
                          'boosting_disabled': ['testdisabled'],
                          'archive_sources': ['testarchive']})

    def test_read_test_corr_libtribler_conf(self):
        old_config = RawConfigParser()
        old_config.read(os.path.join(self.CONFIG_PATH, "libtriblercorrupt70.conf"))
        new_config = TriblerConfig()
        result_config = Tribler.Core.Upgrade.config_converter.convert_libtribler(new_config, old_config)
        self.assertTrue(new_config.get_permid_keypair_filename().endswith("ec.pem"))
        self.assertTrue(len(new_config.get_tunnel_community_socks5_listen_ports()), 5)
        self.assertEqual("collected_metadata", new_config.get_metadata_store_dir())
        self.assertEqual((0, ('127.0.0.1', [-1, -1, -1, -1, -1]), ''), new_config.get_anon_proxy_settings())
        self.assertEqual(result_config.get_credit_mining_sources(), new_config.get_credit_mining_sources())
