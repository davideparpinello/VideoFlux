#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About: Basic example of service (running inside a APPContainer) migration.
"""

import os
import shlex
import time

from subprocess import check_output

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller


def get_ofport(ifce: str):
    """Get the openflow port based on the iterface name.

    :param ifce (str): Name of the interface.
    """
    return (
        check_output(shlex.split("ovs-vsctl get Interface {} ofport".format(ifce)))
        .decode("utf-8")
        .strip()
    )


if __name__ == "__main__":
    # Only used for auto-testing.
    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")

    net = Containernet(controller=Controller, link=TCLink, xterms=False)
    mgr = VNFManager(net)

    try:
        mgr.removeContainer("streaming_server")
        mgr.removeContainer("cache_server_cache1")
        mgr.removeContainer("cache_server_cache2")
        mgr.removeContainer("test_client")
    except Exception as e:
        print(e)
    finally:
        net.stop()
        mgr.stop()
