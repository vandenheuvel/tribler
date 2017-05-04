import ast
from ConfigParser import RawConfigParser
import logging

from Tribler.Core.Config.tribler_config import TriblerConfig
from Tribler.Core.exceptions import InvalidConfigException
logger = logging.getLogger(__name__)


def convert(config):
    """
    Convert the Config files libtribler.conf and tribler.conf to the newer triblerd.conf
    :param: session: The Config which can be used to convert the old files to the new format
    :return: The newly edited Config file with the old Config data inserted.
    """
    libtribler_cfg = RawConfigParser()
    libtribler_cfg.read(TriblerConfig.get_default_state_dir().join("libtribler.conf"))
    config_converted = convert_libtribler(config, libtribler_cfg)

    tribler_cfg = RawConfigParser()
    tribler_cfg.read(TriblerConfig.get_default_state_dir().join("tribler.conf"))
    config_converted = convert_tribler(config_converted, tribler_cfg)
    config_converted.write()
    return config_converted


def convert_tribler(cfg, old_config):
    """
    Add the old values of the tribler.conf file to the newer Config file.
    :param cfg: The Config file to which the old data can be written
    :param old_config: A RawConfigParser containing the old tribler.conf Config file
    :return: The edited Config file
    """
    config = cfg.copy()
    for section in old_config.sections():
        for (name, value) in old_config.items(section):
            temp_config = config.copy()
            if section == "Tribler" and name == "family_filter":
                temp_config.set_family_filter_enabled(value)
            if section == "Tribler" and name == "default_anonymity_enabled":
                temp_config.set_default_anonymity_enabled(value)
            if section == "Tribler" and name == "default_number_hops":
                temp_config.set_default_number_hops(value)
            if section == "downloadconfig" and name == "saveas":
                temp_config.config["download_defaults"]["saveas"] = value
            if section == "downloadconfig" and name == "seeding_mode":
                temp_config.config["download_defaults"]["seeding_mode"] = value
            if section == "downloadconfig" and name == "seeding_ratio":
                temp_config.config["download_defaults"]["seeding_ratio"] = value
            if section == "downloadconfig" and name == "seeding_time":
                temp_config.config["download_defaults"]["seeding_time"] = value
            if section == "downloadconfig" and name == "version":
                temp_config.config["download_defaults"]["version"] = value

            try:
                temp_config.validate()
                config = temp_config
            except InvalidConfigException as exc:
                logger.debug("The following field in the old tribler.conf was wrong: %e" % exc.args)
    return config


def convert_libtribler(cfg, old_config):
    """
    Add the old values of the libtribler.conf file to the newer Config file.
    :param cfg: The Config file to which the old data can be written
    :param old_config: A RawConfigParser containing the old libtribler.conf Config file
    :return: The edited Config file
    """
    config = cfg.copy()
    for section in old_config.sections():
        for (name, value) in old_config.items(section):
            temp_config = config.copy()
            if section == "general" and name == "state_dir":
                temp_config.set_state_dir(value)
            elif section == "general" and name =="eckeypairfilename":
                temp_config.set_permid_keypair_filename(value)
            elif section == "general" and name == "megacache":
                temp_config.set_megacache_enabled(value)
            elif section == "general" and name == "videoanalyserpath":
                temp_config.set_video_analyser_path(value)
            elif section == "allchannel_community" and name == "enabled":
                temp_config.set_channel_search_enabled(value)
            elif section == "channel_community" and name == "enabled":
                temp_config.set_channel_community_enabled(value)
            elif section == "preview_channel_community" and name == "enabled":
                temp_config.set_preview_channel_community_enabled(value)
            elif section == "search_community" and name == "enabled":
                temp_config.set_torrent_search_enabled(value)
            elif section == "tunnel_community" and name == "enabled":
                temp_config.set_tunnel_community_enabled(value)
            elif section == "tunnel_community" and name == "socks5_listen_ports":
                val_literal = ast.literal_eval(value)
                if isinstance(val_literal, list):
                    temp_config.set_tunnel_community_socks5_listen_ports(val_literal)
            elif section == "tunnel_community" and name == "exitnode_enabled":
                temp_config.set_tunnel_community_exitnode_enabled(value)
            elif section == "multichain" and name == "enabled":
                temp_config.set_multichain_enabled(value)
            elif section == "general" and name == "ec_keypair_filename_multichain":
                temp_config.set_multichain_permid_keypair_filename(value)
            elif section == "metadata" and name == "enabled":
                temp_config.set_metadata_enabled(value)
            elif section == "metadata" and name == "store_dir":
                temp_config.set_metadata_store_dir(value)
            elif section == "mainline_dht" and name == "enabled":
                temp_config.set_mainline_dht_enabled(value)
            elif section == "mainline_dht" and name == "store_dir":
                temp_config.set_mainline_dht_store_dir(value)
            elif section == "torrent_checking" and name == "enabled":
                temp_config.set_torrent_checking_enabled(value)
            elif section == "torrent_store" and name == "enabled":
                temp_config.set_torrent_store_enabled(value)
            elif section == "torrent_store" and name == "dir":
                temp_config.set_torrent_store_dir(value)
            elif section == "torrent_collecting" and name == "enabled":
                temp_config.set_torrent_collecting_enabled(value)
            elif section == "torrent_collecting" and name == "torrent_collecting_max_torrents":
                temp_config.set_torrent_collecting_max_torrents(value)
            elif section == "torrent_collecting" and name == "torrent_collecting_dir":
                temp_config.set_torrent_collecting_dir(value)
            elif section == "libtorrent" and name == "lt_proxytype":
                temp_config.config["libtorrent"]["proxy_type"] = value
            elif section == "libtorrent" and name == "lt_proxyserver":
                temp_config.config["libtorrent"]["proxy_server"] = value
            elif section == "libtorrent" and name == "lt_proxyauth":
                temp_config.config["libtorrent"]["proxy_auth"] = value
            elif section == "libtorrent" and name == "max_connections_download":
                temp_config.set_libtorrent_max_conn_download(value)
            elif section == "libtorrent" and name == "max_download_rate":
                temp_config.set_libtorrent_max_download_rate(value)
            elif section == "libtorrent" and name == "max_upload_rate":
                temp_config.set_libtorrent_max_upload_rate(value)
            elif section == "libtorrent" and name == "utp":
                temp_config.set_libtorrent_utp(value)
            elif section == "libtorrent" and name == "anon_listen_port":
                temp_config.set_anon_listen_port(value)
            elif section == "libtorrent" and name == "anon_proxytype":
                temp_config.config["libtorrent"]["anon_proxy_type"] = value
            elif section == "libtorrent" and name == "anon_proxyserver":
                val_literal = ast.literal_eval(value)
                if isinstance(val_literal, tuple) and isinstance(val_literal[1], list):
                    temp_config.config["libtorrent"]["anon_proxy_server_ip"] = val_literal[0]
                    temp_config.config["libtorrent"]["anon_proxy_server_ports"] = [str(port) for port in val_literal[1]]
            elif section == "libtorrent" and name == "anon_proxyauth":
                temp_config.config["libtorrent"]["anon_proxy_auth"] = value
            elif section == "dispersy" and name == "enabled":
                temp_config.set_dispersy_enabled(value)
            elif section == "dispersy" and name == "dispersy_port":
                temp_config.set_dispersy_port(value)
            elif section == "video" and name == "enabled":
                temp_config.set_video_server_enabled(value)
            elif section == "video" and name == "port":
                temp_config.set_video_server_port(value)
            elif section == "upgrader" and name == "enabled":
                temp_config.set_upgrader_enabled(value)
            elif section == "watch_folder" and name == "enabled":
                temp_config.set_watch_folder_enabled(value)
            elif section == "watch_folder" and name == "watch_folder_dir":
                temp_config.set_watch_folder_path(value)
            elif section == "http_api" and name == "enabled":
                temp_config.set_http_api_enabled(value)
            elif section == "http_api" and name == "port":
                temp_config.set_http_api_port(value)
            elif section == "credit_mining" and name == "enabled":
                temp_config.set_credit_mining_enabled(value)
            elif section == "credit_mining" and name == "max_torrents_per_source":
                temp_config.set_credit_mining_max_torrents_per_source(value)
            elif section == "credit_mining" and name == "max_torrents_active":
                temp_config.set_credit_mining_max_torrents_active(value)
            elif section == "credit_mining" and name == "source_interval":
                temp_config.set_credit_mining_source_interval(value)
            elif section == "credit_mining" and name == "swarm_interval":
                temp_config.set_credit_mining_swarm_interval(value)
            elif section == "credit_mining" and name == "share_mode_target":
                temp_config.set_credit_mining_share_mode_target(value)
            elif section == "credit_mining" and name == "tracking_interval":
                temp_config.set_credit_mining_tracking_interval(value)
            elif section == "credit_mining" and name == "logging_interval":
                temp_config.set_credit_mining_logging_interval(value)
            elif section == "credit_mining" and name == "boosting_sources":
                temp_config.set_credit_mining_sources(ast.literal_eval(value), 'boosting_sources')
            elif section == "credit_mining" and name == "boosting_enabled":
                temp_config.set_credit_mining_sources(ast.literal_eval(value), "boosting_enabled")
            elif section == "credit_mining" and name == "boosting_disabled":
                temp_config.set_credit_mining_sources(ast.literal_eval(value), "boosting_disabled")
            elif section == "credit_mining" and name == "archive_sources":
                temp_config.set_credit_mining_sources(ast.literal_eval(value), "archive_sources")
            elif section == "credit_mining" and name == "policy":
                temp_config.set_credit_mining_policy(value)

            try:
                temp_config.validate()
                config = temp_config
            except InvalidConfigException as exc:
                logger.debug("The following field in the old libtribler.conf was wrong: %s" % exc.args)

    return config
