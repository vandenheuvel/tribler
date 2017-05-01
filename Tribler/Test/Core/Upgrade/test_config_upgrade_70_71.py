import os

from Tribler.Test.Core.base_test import TriblerCoreTest


class TestConfigUpgrade70to71(TriblerCoreTest):
    """
    Contains all tests that test the config conversion from 70 to 71.
    """
    from Tribler.Test import Core
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(Core.__file__)), "data/config_files/tribler70.conf")

    def test_read_test_config(self):
        print(open(self.CONFIG_PATH).readlines())
