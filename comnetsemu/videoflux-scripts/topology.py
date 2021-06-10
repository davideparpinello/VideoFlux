#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About: Basic example of service (running inside a APPContainer) migration.
"""

import os
import shlex
import time

from subprocess import check_output

from comnetsemu.cli import CLI, spawnXtermDocker
from comnetsemu.net import Containernet, VNFManager
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.node import Controller
from datetime import datetime


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

    info("*** Add the default controller\n")
    net.addController("c0")

    info("*** Creating server\n")
    server = net.addDockerHost(
        "server",
        dimage="dev_test",
        ip="10.0.0.11/24",
        docker_args={"hostname": "server"},
    )
    
    info("*** Creating caches\n")
    cache1 = net.addDockerHost(
        "cache1",
        dimage="dev_test",
        ip="10.0.0.12/24",
        docker_args={"hostname": "cache1"},
    )
    cache2 = net.addDockerHost(
        "cache2",
        dimage="dev_test",
        ip="10.0.0.12/24",
        docker_args={"hostname": "cache2"},
    )

    info("*** Creating client\n")
    client = net.addDockerHost(
        "client",
        dimage="dev_test",
        ip="10.0.0.13/24",
        docker_args={"hostname": "client", "pid_mode": "host"},
    )

    info("*** Adding switch and links\n")
    s1 = net.addSwitch("s1")
    net.addLinkNamedIfce(s1, server, bw=1000, delay="1ms")
    # Add the interfaces for service traffic.
    net.addLinkNamedIfce(s1, cache1, bw=1000, delay="1ms")
    net.addLinkNamedIfce(s1, cache2, bw=1000, delay="1ms")
    net.addLinkNamedIfce(s1, client, bw=1000, delay="1ms")
    # Add the interface for caches internal traffic.
    net.addLink(
        s1,
        cache1,
        bw=1000,
        delay="1ms",
        intfName1="s1-cache1-int",
        intfName2="cache1-s1-int",
    )
    net.addLink(
        s1,
        cache2,
        bw=1000,
        delay="1ms",
        intfName1="s1-cache2-int",
        intfName2="cache2-s1-int",
    )

    info("\n*** Starting network\n")
    net.start()

    s1_server_port_num = get_ofport("s1-server")
    s1_cache1_port_num = get_ofport("s1-cache1")
    s1_cache2_port_num = get_ofport("s1-cache2")
    s1_client_port_num = get_ofport("s1-client")
    server_mac = server.MAC(intf="server-s1")
    cache1_mac = cache1.MAC(intf="cache1-s1")
    cache2_mac = cache2.MAC(intf="cache2-s1")
    client_mac = client.MAC(intf="client-s1")

    server.setMAC("00:00:00:00:00:11", intf="server-s1")
    cache1.setMAC("00:00:00:00:00:12", intf="cache1-s1")
    cache2.setMAC("00:00:00:00:00:12", intf="cache2-s1")
    client.setMAC("00:00:00:00:00:13", intf="client-s1")

    info("*** Use the subnet 192.168.0.0/24 for internal traffic between cache1 and cache2.\n")
    print("- Internal IP of cache1: 192.168.0.12")
    print("- Internal IP of cache2: 192.168.0.13")
    cache1.cmd("ip addr add 192.168.0.12/24 dev cache1-s1-int")
    cache2.cmd("ip addr add 192.168.0.13/24 dev cache2-s1-int")
    cache1.cmd("ping -c 3 192.168.0.13")

    # INFO: For the simplicity, OpenFlow rules are managed directly via
    # `ovs-ofctl` utility provided by the OvS.
    # For realistic setup, switches should be managed by a remote controller.
    info("*** Add flow to forward traffic from h1 to h2 to switch s1.\n")
    
    

    check_output(
        shlex.split(
            'ovs-ofctl add-flow s1 "in_port={}, actions=output:{}"'.format(
                s1_client_port_num, s1_cache1_port_num
            )
        )
    )

    check_output(
        shlex.split(
            'ovs-ofctl add-flow s1 "in_port={}, actions=output:{}"'.format(
                s1_server_port_num, s1_cache1_port_num
            )
        )
    )

    

    info("*** server ping 10.0.0.12 (cache) with 3 packets: \n")
    ret = cache1.cmd("ping -c 3 10.0.0.12")
    print(ret)

    info("*** Deploy streaming service on server.\n")
    streaming_server = mgr.addContainer(
        "streaming_server",
        "server",
        "davideparpi/nginx-rtmp-server",
        "",
    )
    time.sleep(3)

    info("*** Deploy cache service on cache1.\n")
    cache_server_cache1 = mgr.addContainer(
        "cache_server_cache1",
        "cache1",
        "davideparpi/nginx-hls-cache",
        ""
    )
    time.sleep(3)

    info("*** Deploy test container on client.\n")
    test_client = mgr.addContainer(
        "test_client",
        "client",
        "davideparpi/videoflux-test-client",
        ""
    )
    time.sleep(3)

    

    if not AUTOTEST_MODE:
        spawnXtermDocker("streaming_server")
        spawnXtermDocker("cache_server_cache1")
        spawnXtermDocker("test_client")

    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Starting migration from cache1 to cache2 in 60 seconds...\n")
    time.sleep(60)
    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Deploy cache service on cache2.\n")
    cache_server_cache2 = mgr.addContainer(
        "cache_server_cache2",
        "cache2",
        "davideparpi/nginx-hls-cache",
        ""
    )
    if not AUTOTEST_MODE:
        spawnXtermDocker("cache_server_cache2")

    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Mod the added flow to forward traffic from client to cache2 to switch s1.\n")
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_client_port_num, s1_cache2_port_num
            )
        )
    )
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_server_port_num, s1_cache2_port_num
            )
        )
    )

    time.sleep(3)
    mgr.removeContainer("cache_server_cache1")

    info("*** Starting migration from cache2 to cache1 in 35 seconds...\n")
    time.sleep(35)
    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Deploy cache service on cache1.\n")
    cache_server_cache1 = mgr.addContainer(
        "cache_server_cache1",
        "cache1",
        "davideparpi/nginx-hls-cache",
        ""
    )
    if not AUTOTEST_MODE:
        spawnXtermDocker("cache_server_cache1")

    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Mod the added flow to forward traffic from client to cache1 to switch s1.\n")
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_client_port_num, s1_cache1_port_num
            )
        )
    )
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_server_port_num, s1_cache1_port_num
            )
        )
    )

    time.sleep(3)
    mgr.removeContainer("cache_server_cache2")

    info("*** Starting migration from cache1 to cache2 in 35 seconds...\n")
    time.sleep(35)
    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Deploy cache service on cache2.\n")
    cache_server_cache2 = mgr.addContainer(
        "cache_server_cache2",
        "cache2",
        "davideparpi/nginx-hls-cache",
        ""
    )
    if not AUTOTEST_MODE:
        spawnXtermDocker("cache_server_cache2")

    info("***", (datetime.now()).strftime("%H:%M:%S") ,": Mod the added flow to forward traffic from client to cache2 to switch s1.\n")
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_client_port_num, s1_cache2_port_num
            )
        )
    )
    check_output(
        shlex.split(
            'ovs-ofctl mod-flows s1 "in_port={}, actions=output:{}"'.format(
                s1_server_port_num, s1_cache2_port_num
            )
        )
    )

    time.sleep(3)
    mgr.removeContainer("cache_server_cache1")

    if not AUTOTEST_MODE:
        CLI(net)


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

