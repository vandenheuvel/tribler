import logging
import os
import shutil
from binascii import hexlify
from unittest import skip

from twisted.internet.defer import Deferred

from Tribler.Core.Utilities.network_utils import get_random_port
from Tribler.Core.simpledefs import DOWNLOAD_STATUS_STRINGS, DOWNLOAD_STATUS_DOWNLOADING
from Tribler.Test.common import UBUNTU_1504_INFOHASH, TORRENT_UBUNTU_FILE
from Tribler.Test.test_as_server import TestAsServer
from Tribler.Test.twisted_thread import deferred


class TestDownload(TestAsServer):

    """
    Testing of a torrent download via new tribler API:
    """

    def __init__(self, *argv, **kwargs):
        super(TestDownload, self).__init__(*argv, **kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.test_deferred = Deferred()

    def setUpPreSession(self):
        super(TestDownload, self).setUpPreSession()

        self.config.set_downloading_enabled(True)
        self.config.set_dispersy_enabled(False)
        self.config.set_libtorrent_max_conn_download(2)

    def on_download(self, download):
        self._logger.debug("download started: %s", download)
        download.set_state_callback(self.downloader_state_callback)

    @deferred(timeout=60)
    def test_download_torrent_from_url(self):
        # Setup file server to serve torrent file
        files_path = os.path.join(self.session_base_dir, 'http_torrent_files')
        os.mkdir(files_path)
        shutil.copyfile(TORRENT_UBUNTU_FILE, os.path.join(files_path, 'ubuntu.torrent'))
        file_server_port = get_random_port()
        self.setUpFileServer(file_server_port, files_path)

        d = self.session.start_download_from_uri('http://localhost:%s/ubuntu.torrent' % file_server_port)
        d.addCallback(self.on_download)
        return self.test_deferred

    @skip("Fetching a torrent from the external network is unreliable")
    @deferred(timeout=60)
    def test_download_torrent_from_magnet(self):
        magnet_link = 'magnet:?xt=urn:btih:%s' % hexlify(UBUNTU_1504_INFOHASH)
        d = self.session.start_download_from_uri(magnet_link)
        d.addCallback(self.on_download)
        return self.test_deferred

    @deferred(timeout=60)
    def test_download_torrent_from_file(self):
        from urllib import pathname2url
        d = self.session.start_download_from_uri('file:' + pathname2url(TORRENT_UBUNTU_FILE))
        d.addCallback(self.on_download)
        return self.test_deferred

    def downloader_state_callback(self, ds):
        d = ds.get_download()
        self._logger.debug("download status: %s %s %s",
                           repr(d.get_torrent().get_name()),
                           DOWNLOAD_STATUS_STRINGS[ds.get_status()],
                           ds.get_progress())

        if ds.get_status() == DOWNLOAD_STATUS_DOWNLOADING:
            self.test_deferred.callback(None)
            return 0.0, False

        return 1.0, False
