"""
A wrapper around libtorrent
"""
import binascii
import logging
import os
import random
import tempfile
import threading
import time
from copy import deepcopy
from distutils.version import LooseVersion
from shutil import rmtree
from urllib import url2pathname

import libtorrent
from twisted.internet import reactor, threads
from twisted.internet.defer import succeed, fail
from twisted.python.failure import Failure

from Tribler.Core.download.DownloadConfig import DownloadConfig
from Tribler.Core.TorrentDef import TorrentDef, TorrentDefNoMetainfo
from Tribler.Core.Utilities.utilities import parse_magnetlink, fix_torrent
from Tribler.Core.download.DownloadHandle import DownloadHandle
from Tribler.Core.exceptions import DuplicateDownloadException, TorrentFileException
from Tribler.Core.simpledefs import (NTFY_INSERT, NTFY_MAGNET_CLOSE, NTFY_MAGNET_GOT_PEERS, NTFY_REACHABLE,
                                     NTFY_TORRENTS, NTFY_MAGNET_STARTED)
from Tribler.Core.version import version_id
from Tribler.dispersy.taskmanager import LoopingCall, TaskManager
from Tribler.dispersy.util import blocking_call_on_reactor_thread, call_on_reactor_thread

LTSTATE_FILENAME = "lt.state"
METAINFO_CACHE_PERIOD = 5 * 60
DHT_CHECK_RETRIES = 1
DEFAULT_DHT_ROUTERS = [
    ("dht.libtorrent.org", 25401),
    ("router.bittorrent.com", 6881),
    ("router.utorrent.com", 6881)
]
DEFAULT_LIBTORRENT_EXTENSIONS = [
    libtorrent.create_metadata_plugin,
    libtorrent.create_ut_metadata_plugin,
    libtorrent.create_ut_pex_plugin,
    libtorrent.create_smart_ban_plugin
]


class DownloadSessionManager(TaskManager):
    """
    Holds a libtorrent session for every number of hops being used.
    """
    def __init__(self, tribler_session):
        super(DownloadSessionManager, self).__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.tribler_session = tribler_session
        self.libtorrent_sessions = {}

        self.notifier = tribler_session.notifier

        self.set_upload_rate_limit(0)
        self.set_download_rate_limit(0)

        self.torrents = {}

        self.upnp_mapping_dict = {}

        self.dht_ready = False

        self.metadata_tmpdir = None
        self.metainfo_requests = {}
        self.metainfo_lock = threading.RLock()
        self.metainfo_cache = {}

        self.process_alerts_lc = self.register_task("process_alerts", LoopingCall(self._task_process_alerts))
        self.check_reachability_lc = self.register_task("check_reachability", LoopingCall(self._check_reachability))

        self.default_alert_mask = libtorrent.alert.category_t.stats_notification | libtorrent.alert.category_t.error_notification | \
                                  libtorrent.alert.category_t.status_notification | libtorrent.alert.category_t.storage_notification | \
                                  libtorrent.alert.category_t.performance_warning | libtorrent.alert.category_t.tracker_notification
        self.alert_callback = None

    @blocking_call_on_reactor_thread
    def initialize(self):
        # start upnp
        self.get_session().start_upnp()
        self.libtorrent_session_metainfo = self.create_session(hops=0, store_listen_port=False)

        # make temporary directory for metadata collecting through DHT
        self.metadata_tmpdir = tempfile.mkdtemp(suffix=u'tribler_metainfo_tmpdir')

        # register tasks
        self.process_alerts_lc.start(1, now=False)
        self.check_reachability_lc.start(5, now=True)
        self._schedule_next_check(5, DHT_CHECK_RETRIES)

        self.register_task(u'task_cleanup_metacache',
                           LoopingCall(self._task_cleanup_metainfo_cache)).start(60, now=True)

    @blocking_call_on_reactor_thread
    def shutdown(self):
        self.cancel_all_pending_tasks()

        # remove all upnp mapping
        for upnp_handle in self.upnp_mapping_dict.itervalues():
            self.get_session().delete_port_mapping(upnp_handle)
        self.upnp_mapping_dict = None

        self.get_session().stop_upnp()

        # Save libtorrent state
        libtorrent_state_file = open(os.path.join(self.tribler_session.config.get_state_dir(), LTSTATE_FILENAME), 'w')
        libtorrent_state_file.write(libtorrent.bencode(self.get_session().save_state()))
        libtorrent_state_file.close()

        for libtorrent_session in self.libtorrent_sessions.itervalues():
            del libtorrent_session
        self.libtorrent_sessions = None

        # remove metadata temporary directory
        rmtree(self.metadata_tmpdir)
        self.metadata_tmpdir = None

        self.tribler_session = None

    def create_session(self, hops=0, store_listen_port=True):
        settings = {}

        # Due to a bug in download 0.16.18, the outgoing_port and num_outgoing_ports value should be set in
        # the settings dictionary
        settings['outgoing_port'] = 0
        settings['num_outgoing_ports'] = 1

        # Copy construct so we don't modify the default list
        extensions = list(DEFAULT_LIBTORRENT_EXTENSIONS)

        # Elric: Strip out the -rcX, -beta, -whatever tail on the version string.
        fingerprint = ['TL'] + map(int, version_id.split('-')[0].split('.')) + [0]
        ltsession = lt.session(lt.fingerprint(*fingerprint), flags=0) if hops == 0 else lt.session(flags=0)

        if hops == 0:
            settings['user_agent'] = 'Tribler/' + version_id
            # Elric: Strip out the -rcX, -beta, -whatever tail on the version string.
            fingerprint = ['TL'] + map(int, version_id.split('-')[0].split('.')) + [0]
            # Workaround for libtorrent 0.16.3 segfault (see https://code.google.com/p/libtorrent/issues/detail?id=369)
            libtorrent_session = libtorrent.session(libtorrent.fingerprint(*fingerprint), flags=0)
            enable_utp = self.tribler_session.config.get_downloading_utp_enabled()
            settings['enable_outgoing_utp'] = enable_utp
            settings['enable_incoming_utp'] = enable_utp

            if LooseVersion(self.get_libtorrent_version()) >= LooseVersion("1.1.0"):
                settings['prefer_rc4'] = True
                settings["listen_interfaces"] = "0.0.0.0:%d" % self.tribler_session.config.get_libtorrent_port()
            else:
                pe_settings = lt.pe_settings()
                pe_settings.prefer_rc4 = True
                ltsession.set_pe_settings(pe_settings)
        else:
            settings['enable_outgoing_utp'] = True
            settings['enable_incoming_utp'] = True
            settings['enable_outgoing_tcp'] = False
            settings['enable_incoming_tcp'] = False
            settings['anonymous_mode'] = True
            settings['force_proxy'] = True

            if LooseVersion(self.get_libtorrent_version()) >= LooseVersion("1.1.0"):
                settings["listen_interfaces"] = "0.0.0.0:%d" % self.tribler_session.config.get_anon_listen_port()

            # No PEX for anonymous sessions
            libtorrent_session = libtorrent.session(flags=0)
            libtorrent_session.add_extension(libtorrent.create_ut_metadata_plugin)
            libtorrent_session.add_extension(libtorrent.create_smart_ban_plugin)

        libtorrent_session.set_settings(settings)
        libtorrent_session.set_alert_mask(libtorrent.alert.category_t.stats_notification |
                                 libtorrent.alert.category_t.error_notification |
                                 libtorrent.alert.category_t.status_notification |
                                 libtorrent.alert.category_t.storage_notification |
                                 libtorrent.alert.category_t.performance_warning |
                                 libtorrent.alert.category_t.tracker_notification)

        # Load proxy settings
        if hops == 0:
            proxy_settings = self.tribler_session.config.get_downloading_proxy_settings()
        else:
            proxy_settings = list(self.tribler_session.config.get_anon_proxy_settings())
            proxy_host, proxy_ports = proxy_settings[1]
            proxy_settings[1] = (proxy_host, proxy_ports[hops - 1])
        self.set_proxy_settings(libtorrent_session, *proxy_settings)

        for extension in extensions:
            libtorrent_session.add_extension(extension)

        # Set listen port & start the DHT
        if hops == 0:
            listen_port = self.tribler_session.config.get_downloading_port()
            libtorrent_session.listen_on(listen_port, listen_port + 10)
            if listen_port != libtorrent_session.listen_port() and store_listen_port:
                self.tribler_session.config.set_downloading_port_runtime(libtorrent_session.listen_port())
            try:
                libtorrent_state = libtorrent.bdecode(
                    open(os.path.join(self.tribler_session.config.get_state_dir(), LTSTATE_FILENAME)).read())
                if libtorrent_state is not None:
                    libtorrent_session.load_state(libtorrent_state)
                else:
                    self._logger.warning("the lt.state appears to be corrupt, writing new data on shutdown")
            except Exception, exc:
                self._logger.info("could not load libtorrent state, got exception: %r. starting from scratch" % exc)
            libtorrent_session.start_dht()
        else:
            libtorrent_session.listen_on(self.tribler_session.config.get_anon_listen_port(),
                                self.tribler_session.config.get_anon_listen_port() + 20)
            libtorrent_session.start_dht()

            libtorrent_session_settings = libtorrent_session.get_settings()
            libtorrent_session_settings['upload_rate_limit'] = self.tribler_session.config.get_downloading_max_upload_rate()
            libtorrent_session_settings['download_rate_limit'] = self.tribler_session.config.get_downloading_max_download_rate()
            libtorrent_session.set_settings(libtorrent_session_settings)

        for router in DEFAULT_DHT_ROUTERS:
            libtorrent_session.add_dht_router(*router)

        self._logger.debug("Started libtorrent session for %d hops on port %d", hops, libtorrent_session.listen_port())

        return libtorrent_session

    def get_session(self, hops=0):
        if hops not in self.libtorrent_sessions:
            self.libtorrent_sessions[hops] = self.create_session(hops)

        return self.libtorrent_sessions[hops]

    def get_settings(self, hops=0):
        return self.get_session(hops).get_settings()

    def set_proxy_settings(self, libtorrent_session, ptype, proxy_server_ip=None, proxy_server_port=None, auth=None):
        proxy_settings = libtorrent.proxy_settings()
        proxy_settings.type = libtorrent.proxy_type(ptype)
        if proxy_server_ip and proxy_server_port:
            proxy_settings.hostname = proxy_server_ip
            proxy_settings.port = proxy_server_port
        if auth:
            proxy_settings.username = auth[0]
            proxy_settings.password = auth[1]
        proxy_settings.proxy_hostnames = True
        proxy_settings.proxy_peer_connections = True

        if libtorrent_session is not None:
            libtorrent_session.set_proxy(proxy_settings)
        else:
            # only apply the proxy settings to normal libtorrent session (with hops = 0)
            self.libtorrent_sessions[0].set_proxy(proxy_settings)

    def set_utp(self, enable, hops=None):
        def do_set_utp(libtorrent_session):
            settings = libtorrent_session.get_settings()
            settings['enable_outgoing_utp'] = enable
            settings['enable_incoming_utp'] = enable
            libtorrent_session.set_settings(settings)

        if hops is None:
            for libtorrent_session in self.libtorrent_sessions.itervalues():
                do_set_utp(libtorrent_session)
        else:
            do_set_utp(self.get_session(hops))

    def set_max_connections(self, conns, hops=None):
        self._map_call_on_libtorrent_sessions(hops, 'set_max_connections', conns)

    def set_upload_rate_limit(self, rate, hops=None):
        # Rate conversion due to the fact that we had a different system with Swift
        # and the old python BitTorrent core: unlimited == 0, stop == -1, else rate in kbytes
        libtorrent_rate = int(-1 if rate == 0 else (1 if rate == -1 else rate * 1024))

        # Pass outgoing_port and num_outgoing_ports to dict due to bug in libtorrent 0.16.18
        settings_dict = {'upload_rate_limit': libtorrent_rate, 'outgoing_port': 0, 'num_outgoing_ports': 1}
        self._map_call_on_libtorrent_sessions(hops, 'set_settings', settings_dict)

    def get_upload_rate_limit(self, hops=None):
        # Rate conversion due to the fact that we had a different system with Swift
        # and the old python BitTorrent core: unlimited == 0, stop == -1, else rate in kbytes
        libtorrent_rate = self.get_session(hops).upload_rate_limit()
        return 0 if libtorrent_rate == -1 else (-1 if libtorrent_rate == 1 else libtorrent_rate / 1024)

    def set_download_rate_limit(self, rate, hops=None):
        libtorrent_rate = int(-1 if rate == 0 else (1 if rate == -1 else rate * 1024))

        # Pass outgoing_port and num_outgoing_ports to dict due to bug in libtorrent 0.16.18
        settings_dict = {'download_rate_limit': libtorrent_rate}
        self._map_call_on_libtorrent_sessions(hops, 'set_settings', settings_dict)

    def get_download_rate_limit(self, hops=0):
        libtorrent_rate = self.get_session(hops).download_rate_limit()
        return 0 if libtorrent_rate == -1 else (-1 if libtorrent_rate == 1 else libtorrent_rate / 1024)

    def is_dht_ready(self):
        return self.dht_ready

    def add_torrent(self, torrentdl, atp):
        # If we are collecting the torrent for this infohash, abort this first.
        with self.metainfo_lock:
            libtorrent_session = self.get_session(atp.pop('hops', 0))

            if 'ti' in atp:
                info_hash = str(atp['ti'].info_hash())
            elif 'url' in atp:
                info_hash = binascii.hexlify(parse_magnetlink(atp['url'])[1])
            else:
                raise ValueError('No ti or url key in add_torrent_params')

            # Check if we added this torrent before
            known = [str(h.info_hash()) for h in libtorrent_session.get_torrents()]
            if info_hash in known:
                self.torrents[info_hash] = (torrentdl, libtorrent_session)
                infohash_bin = binascii.unhexlify(info_hash)
                return libtorrent_session.find_torrent(libtorrent.big_number(infohash_bin))

            # Otherwise, add it anew
            libtorrent_torrent_handle = libtorrent_session.add_torrent(encode_atp(atp))
            download_handle = DownloadHandle(libtorrent_torrent_handle)
            info_hash = str(download_handle.info_hash())
            if info_hash in self.torrents:
                raise DuplicateDownloadException("This download already exists.")
            self.torrents[info_hash] = (torrentdl, libtorrent_session)

            self._logger.debug("added torrent %s", info_hash)

            return download_handle

    def remove_torrent(self, torrentdl, removecontent=False):
        """
        Start removing a torrent, the process is completed when a 'torrent_removed_alert'
        is received in 'process_alert'.
        """
        handle = torrentdl.handle
        if handle and handle.is_valid():
            infohash = str(handle.info_hash())
            if infohash in self.torrents:
                self.torrents[infohash][1].remove_torrent(handle, int(removecontent))
                out = self.torrents[infohash][0].deferred_removed
                self._logger.debug("remove torrent %s", infohash)
                return out
            else:
                self._logger.debug("cannot remove torrent %s because it does not exists", infohash)
        else:
            self._logger.debug("cannot remove invalid torrent")
        # Always return a Deferred, in this case it has already been called
        return succeed(None)

    def add_upnp_mapping(self, port, protocol='TCP'):
        # TODO martijn: this check should be removed once we do not support libtorrent versions that do not have the
        # add_port_mapping method exposed in the Python bindings
        if hasattr(self.get_session(), 'add_port_mapping'):
            protocol_name = protocol.lower()
            assert protocol_name in (u'udp', u'tcp'), "protocol is neither UDP nor TCP: %s" % repr(protocol)

            from libtorrent import protocol_type
            protocol_type_obj = protocol_type.udp if protocol_name == 'udp' else protocol_type.tcp
            upnp_handle = self.get_session().add_port_mapping(protocol_type_obj, port, port)
            self.upnp_mapping_dict[(port, protocol_name)] = upnp_handle

            self._logger.info(u"uPnP port added : %s %s", port, protocol_name)
        else:
            self._logger.warning("port mapping method not exposed in libtorrent")

    def process_alert(self, alert):
        alert_type = str(type(alert)).split("'")[1].split(".")[-1]
        handle = getattr(alert, 'handle', None)
        if handle and handle.is_valid():
            infohash = str(handle.info_hash())
            if infohash in self.torrents:
                self.torrents[infohash][0].process_alert(alert, alert_type)
            elif infohash in self.metainfo_requests:
                if isinstance(alert, libtorrent.metadata_received_alert):
                    self.got_metainfo(infohash)
            else:
                self._logger.debug("LibtorrentMgr: could not find torrent %s", infohash)

        if alert_type == 'torrent_removed_alert':
            info_hash = str(alert.info_hash)
            if info_hash in self.torrents:
                deferred = self.torrents[info_hash][0].deferred_removed
                del self.torrents[info_hash]
                deferred.callback(None)
                self._logger.debug("LibtorrentMgr: ['torrent_removed_alert'] removed torrent %s", info_hash)
            else:
                if alert_type == 'torrent_removed_alert':
                    info_hash = str(alert.info_hash)
                    if info_hash in self.torrents:
                        deferred = self.torrents[info_hash][0].deferred_removed
                        del self.torrents[info_hash]
                        deferred.callback(None)
                    else:
                        self._logger.debug("LibtorrentMgr: ['torrent_removed_alert'] invalid torrent %s", info_hash)
                self._logger.debug("Alert for invalid torrent")
        if self.alert_callback:
            self.alert_callback(alert)

    def get_metainfo(self, infohash_or_magnet, callback, timeout=30, timeout_callback=None, notify=True):
        if not self.is_dht_ready() and timeout > 5:
            self._logger.info("DHT not ready, rescheduling get_metainfo")

            def schedule_call():
                random_id = ''.join(random.choice('0123456789abcdef') for _ in xrange(30))
                self.register_task("schedule_metainfo_lookup_%s" % random_id,
                                   reactor.callLater(5, lambda i=infohash_or_magnet, c=callback, t=timeout - 5,
                                                  tcb=timeout_callback, n=notify: self.get_metainfo(i, c, t, tcb, n)))

            reactor.callFromThread(schedule_call)
            return

        magnet = infohash_or_magnet if infohash_or_magnet.startswith('magnet') else None
        infohash_bin = infohash_or_magnet if not magnet else parse_magnetlink(magnet)[1]
        infohash = binascii.hexlify(infohash_bin)

        if infohash in self.torrents:
            return

        with self.metainfo_lock:
            self._logger.debug('get_metainfo %s %s %s', infohash_or_magnet, callback, timeout)

            cache_result = self._get_cached_metainfo(infohash)
            if cache_result:
                callback(deepcopy(cache_result))

            elif infohash not in self.metainfo_requests:
                # Flags = 4 (upload mode), should prevent libtorrent from creating files
                atp = {'save_path': self.metadata_tmpdir,
                       'flags': (libtorrent.add_torrent_params_flags_t.flag_duplicate_is_error |
                                 libtorrent.add_torrent_params_flags_t.flag_upload_mode)}
                if magnet:
                    atp['url'] = magnet
                else:
                    atp['info_hash'] = libtorrent.big_number(infohash_bin)
                try:
                    handle = self.libtorrent_session_metainfo.add_torrent(encode_atp(atp))
                except TypeError as e:
                    self._logger.warning("Failed to add torrent with infohash %s, "
                                         "attempting to use it as it is and hoping for the best",
                                         binascii.hexlify(infohash_bin))
                    self._logger.warning("Error was: %s", e)
                    atp['info_hash'] = infohash_bin
                    handle = self.libtorrent_session_metainfo.add_torrent(encode_atp(atp))

                if notify:
                    self.notifier.notify(NTFY_TORRENTS, NTFY_MAGNET_STARTED, infohash_bin)

                self.metainfo_requests[infohash] = {'handle': handle,
                                                    'callbacks': [callback],
                                                    'timeout_callbacks': [timeout_callback] if timeout_callback else [],
                                                    'notify': notify}

                # if the handle is valid and already has metadata which is the case when torrent already exists in
                # session then metadata_received_alert is not fired so we call self.got_metainfo() directly here
                if handle.is_valid() and handle.has_metadata():
                    self.got_metainfo(infohash, timeout=False)
                    return

                def schedule_call():
                    random_id = ''.join(random.choice('0123456789abcdef') for _ in xrange(30))
                    self.register_task("schedule_got_metainfo_lookup_%s" % random_id,
                                       reactor.callLater(timeout, lambda: self.got_metainfo(infohash, timeout=True)))

                reactor.callFromThread(schedule_call)
            else:
                self.metainfo_requests[infohash]['notify'] = self.metainfo_requests[infohash]['notify'] and notify
                callbacks = self.metainfo_requests[infohash]['callbacks']
                if callback not in callbacks:
                    callbacks.append(callback)
                else:
                    self._logger.debug('get_metainfo duplicate detected, ignoring')

    def got_metainfo(self, infohash, timeout=False):
        with self.metainfo_lock:
            infohash_bin = binascii.unhexlify(infohash)

            if infohash in self.metainfo_requests:
                request_dict = self.metainfo_requests.pop(infohash)
                handle = request_dict['handle']
                callbacks = request_dict['callbacks']
                timeout_callbacks = request_dict['timeout_callbacks']
                notify = request_dict['notify']

                self._logger.debug('got_metainfo %s %s %s', infohash, handle, timeout)

                assert handle
                if handle:
                    if callbacks and not timeout:
                        metainfo = {"info": libtorrent.bdecode(handle.get_info().metadata())}
                        trackers = [tracker.url for tracker in handle.get_info().trackers()]
                        peers = []
                        leechers = 0
                        seeders = 0
                        for peer in handle.get_peer_info():
                            peers.append(peer.ip)
                            if peer.progress == 1:
                                seeders += 1
                            else:
                                leechers += 1

                        if trackers:
                            if len(trackers) > 1:
                                metainfo["announce-list"] = [trackers]
                            metainfo["announce"] = trackers[0]
                        else:
                            metainfo["nodes"] = []
                        if peers and notify:
                            self.notifier.notify(NTFY_TORRENTS, NTFY_MAGNET_GOT_PEERS, infohash_bin, len(peers))
                        metainfo["initial peers"] = peers
                        metainfo["leechers"] = leechers
                        metainfo["seeders"] = seeders

                        self._add_cached_metainfo(infohash, metainfo)

                        for callback in callbacks:
                            callback(deepcopy(metainfo))

                        # let's not print the hashes of the pieces
                        debuginfo = deepcopy(metainfo)
                        del debuginfo['info']['pieces']
                        self._logger.debug('got_metainfo result %s', debuginfo)

                    elif timeout_callbacks and timeout:
                        for callback in timeout_callbacks:
                            callback(infohash_bin)

                if handle:
                    self.libtorrent_session_metainfo.remove_torrent(handle, 1)
                    if notify:
                        self.notifier.notify(NTFY_TORRENTS, NTFY_MAGNET_CLOSE, infohash_bin)

    def _get_cached_metainfo(self, infohash):
        if infohash in self.metainfo_cache:
            return self.metainfo_cache[infohash]['meta_info']

    def _add_cached_metainfo(self, infohash, metainfo):
        self.metainfo_cache[infohash] = {'time': time.time(),
                                         'meta_info': metainfo}

    def _task_cleanup_metainfo_cache(self):
        oldest_time = time.time() - METAINFO_CACHE_PERIOD

        for info_hash, values in self.metainfo_cache.items():
            last_time, metainfo = values
            if last_time < oldest_time:
                del self.metainfo_cache[info_hash]

    def _task_process_alerts(self):
        for libtorrent_session in self.libtorrent_sessions.itervalues():
            if libtorrent_session:
                for alert in libtorrent_session.pop_alerts():
                    self.process_alert(alert)

        # We have a separate session for metainfo requests.
        # For this session we are only interested in the metadata_received_alert.
        if self.libtorrent_session_metainfo:
            for alert in self.libtorrent_session_metainfo.pop_alerts():
                if isinstance(alert, libtorrent.metadata_received_alert):
                    self.got_metainfo(str(alert.handle.info_hash()))

    def _check_reachability(self):
        if self.get_session() and self.get_session().get_status().has_incoming_connections:
            self.notifier.notify(NTFY_REACHABLE, NTFY_INSERT, None, '')
            self.check_reachability_lc.stop()

    @call_on_reactor_thread
    def _schedule_next_check(self, delay, retries_left):
        self.register_task(u'check_dht', reactor.callLater(delay, self.do_dht_check, retries_left))

    def do_dht_check(self, retries_left):
        # Sometimes the dht fails to start. To workaround this issue we monitor the #dht_nodes, and restart if needed.

        libtorrent_session = self.get_session()
        dht_nodes = libtorrent_session.status().dht_nodes
        if dht_nodes <= 25:
            if dht_nodes >= 5 and retries_left > 0:
                self._logger.info(u"No enough DHT nodes %s, will try again", dht_nodes)
                self._schedule_next_check(5, retries_left - 1)
            else:
                self._logger.info(u"No enough DHT nodes %s, will restart DHT", dht_nodes)
                threads.deferToThread(libtorrent_session.start_dht)
                self._schedule_next_check(10, 1)
        else:
            self._logger.info("dht is working enough nodes are found (%d)", dht_nodes)
            self.dht_ready = True

    def _map_call_on_libtorrent_sessions(self, hops, funcname, *args, **kwargs):
        if hops is None:
            for session in self.libtorrent_sessions.itervalues():
                getattr(session, funcname)(*args, **kwargs)
        else:
            getattr(self.get_session(hops), funcname)(*args, **kwargs)

    def start_download_from_uri(self, uri, download_config=None):
        if uri.startswith("http"):
            return self.start_download_from_url(bytes(uri), download_config=download_config)
        if uri.startswith("magnet:"):
            return succeed(self.start_download_from_magnet(uri, download_config=download_config))
        if uri.startswith("file:"):
            argument = url2pathname(uri[5:])
            return succeed(self.start_download(torrent_filename=argument, download_config=download_config))

        return fail(Failure(Exception("invalid uri")))

    @blocking_call_on_reactor_thread
    def start_download_from_url(self, url, download_config=None):

        def _on_loaded(tdef):
            return self.start_download(torrent_filename=None, infohash=None, tdef=tdef, download_config=download_config)

        deferred = TorrentDef.load_from_url(url)
        deferred.addCallback(_on_loaded)
        return deferred

    def start_download_from_magnet(self, url, download_config=None):
        name, infohash, _ = parse_magnetlink(url)
        if name is None:
            name = "Unknown name"
        if infohash is None:
            raise RuntimeError("Missing infohash")
        tdef = TorrentDefNoMetainfo(infohash, name, url=url)
        return self.start_download(tdef=tdef, download_config=download_config)

    def start_download(self, torrent_filename=None, infohash=None, tdef=None, download_config=None):
        self._logger.debug(u"starting download: filename: %s, torrent def: %s", torrent_filename, tdef)

        if infohash is not None:
            assert isinstance(infohash, str), "infohash type: %s" % type(infohash)
            assert len(infohash) == 20, "infohash length is not 20: %s, %s" % (len(infohash), infohash)

        # the priority of the parameters is: (1) tdef, (2) infohash, (3) torrent_file.
        # so if we have tdef, infohash and torrent_file will be ignored, and so on.
        if tdef is None:
            if infohash is not None:
                # try to get the torrent from torrent_store if the infohash is provided
                torrent_data = self.tribler_session.get_collected_torrent(infohash)
                if torrent_data is not None:
                    # use this torrent data for downloading
                    tdef = TorrentDef.load_from_memory(torrent_data)

            if tdef is None:
                assert torrent_filename is not None, "torrent file must be provided if tdef and infohash are not given"
                # try to get the torrent from the given torrent file
                torrent_data = fix_torrent(torrent_filename)
                if torrent_data is None:
                    raise TorrentFileException("error while decoding torrent file")

                tdef = TorrentDef.load_from_memory(torrent_data)

        assert tdef is not None, "tdef MUST not be None after loading torrent"

        d = self.tribler_session.get_download(tdef.get_infohash())
        if d:
            new_trackers = list(set(tdef.get_trackers_as_single_tuple()) - set(
                d.get_torrent().get_trackers_as_single_tuple()))
            if not new_trackers:
                raise DuplicateDownloadException("This download already exists.")

            else:
                self.tribler_session.update_trackers(tdef.get_infohash(), new_trackers)
            return

        download_config = download_config or DownloadConfig()

        self._logger.info('start_download: Starting in VOD mode')
        result = self.tribler_session.start_download_from_tdef(tdef, download_config)

        return result

    def get_libtorrent_version(self):
        """
        This method returns the version of the used libtorrent
        library and is required for compatibility purposes
        """
        if hasattr(libtorrent, '__version__'):
            return libtorrent.__version__
        else:
            # libtorrent.version is deprecated starting from 1.0
            return libtorrent.version

    def update_max_rates_from_config(self):
        """
        Set the maximum download and maximum upload rate limits with the value in the config.

        This is the extra step necessary to apply a new maximum download/upload rate setting.
        :return:
        """
        for libtorrent_session in self.libtorrent_sessions.itervalues():
            libtorrent_session_settings = libtorrent_session.get_settings()
            libtorrent_session_settings['download_rate_limit'] = self.tribler_session.config.get_downloading_max_download_rate()
            libtorrent_session_settings['upload_rate_limit'] = self.tribler_session.config.get_downloading_max_upload_rate()
            libtorrent_session.set_settings(libtorrent_session_settings)


def encode_atp(atp):
    for k, v in atp.iteritems():
        if isinstance(v, unicode):
            atp[k] = v.encode('utf-8')
    return atp
