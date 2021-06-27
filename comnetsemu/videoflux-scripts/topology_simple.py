#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
About: Simple topology of service migration using Appcontainer
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

def log_message(message: str):
    """Print a log message with a timestamp.

    :param message (str): string containing the message.
    """

    info("*** ", (datetime.now()).strftime("%H:%M:%S") ,": ", message ,"\n")
    return


if __name__ == "__main__":

    # Only used for auto-testing.
    AUTOTEST_MODE = os.environ.get("COMNETSEMU_AUTOTEST_MODE", 0)

    setLogLevel("info")

    net = Containernet(controller=Controller, link=TCLink, xterms=False)
    mgr = VNFManager(net)

    log_message("Add the default controller")
    net.addController("c0")

    log_message("Creating server")
    server = net.addDockerHost(
        "server",
        dimage="dev_test",
        ip="10.0.0.11/24",
        docker_args={"hostname": "server"},
    )
    
    log_message("Creating caches")
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

    log_message("Creating client")
    client = net.addDockerHost(
        "client",
        dimage="dev_test",
        ip="10.0.0.13/24",
        docker_args={"hostname": "client", "pid_mode": "host"},
    )

    log_message("Adding switch and links\n")
    s1 = net.addSwitch("s1")
    net.addLinkNamedIfce(s1, server, bw=1000, delay="1ms")
    # Add the interfaces for service traffic.
    net.addLinkNamedIfce(s1, cache1, bw=1000, delay="1ms")
    net.addLinkNamedIfce(s1, cache2, bw=1000, delay="1ms")
    net.addLinkNamedIfce(s1, client, bw=1000, delay="1ms")

    log_message("\nStarting network")
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

    # INFO: For the simplicity, OpenFlow rules are managed directly via
    # `ovs-ofctl` utility provided by the OvS.
    # For realistic setup, switches should be managed by a remote controller.
    log_message("Add flow to forward traffic from h1 to h2 to switch s1.")

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

    

    log_message("client ping 10.0.0.12 (cache) with 3 packets:")
    ret = client.cmd("ping -c 3 10.0.0.12")
    print(ret)

    time.sleep(3)

    log_message("Deploy streaming service on server.")
    streaming_server = mgr.addContainer(
        "streaming_server",
        "server",
        "davideparpi/nginx-rtmp-server",
        "",
    )
    log_message("Deploy cache service on cache1.")
    cache_server_cache1 = mgr.addContainer(
        "cache_server_cache1",
        "cache1",
        "davideparpi/nginx-hls-cache",
        ""
    )
    log_message("Deploy test container on client.")

    env_str = "DISPLAY=" + os.environ['DISPLAY'] # The X11 display IP will be the same of the Virtual Machine
    
    test_client = mgr.addContainer(
        "test_client",
        "client",
        "davideparpi/videoflux-test-client",
        "",
        docker_args={"environment": [env_str]}
    )    

    if not AUTOTEST_MODE:
        spawnXtermDocker("streaming_server")
        spawnXtermDocker("cache_server_cache1")
        spawnXtermDocker("test_client")

    choice = 0
    while choice not in range(1,3):
        print("\nDo you want to start the migration or skip and go to the Mininet CLI?")
        print("----------------------------\n")
        print("1) start the migration")
        print("2) skip and go to Mininet CLI\n")
        choice = int(input("Enter your choice: "))
        if(choice not in range(1,3)):
            print("\nYour choiche is not correct. Retry\n")

    if choice == 1 :

        log_message("Starting migration from cache1 to cache2 in 30 seconds...")
        time.sleep(30)
        
        log_message("Deploy cache service on cache2.")
        start_time = time.time()
        cache_server_cache2 = mgr.addContainer(
            "cache_server_cache2",
            "cache2",
            "davideparpi/nginx-hls-cache",
            ""
        )
        if not AUTOTEST_MODE:
            spawnXtermDocker("cache_server_cache2")
        
        

        log_message("Mod the added flow to forward traffic from client to cache2 to switch s1.")
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
        
        print("--- Migration took %s seconds ---" % (time.time() - start_time))
        log_message("client ping 10.0.0.12 (cache) with 10 packets:")
        ret = client.cmd("ping -c 10 10.0.0.12")
        print(ret)

        time.sleep(3)
        mgr.removeContainer("cache_server_cache1")

        restart = 0

        if(restart == 0):

            log_message("Starting migration from cache2 to cache1 in 30 seconds...")
            time.sleep(30)
            log_message("Deploy cache service on cache1.")
            start_time = time.time()
            cache_server_cache1 = mgr.addContainer(
                "cache_server_cache1",
                "cache1",
                "davideparpi/nginx-hls-cache",
                ""
            )
            if not AUTOTEST_MODE:
                spawnXtermDocker("cache_server_cache1")

            log_message("Mod the added flow to forward traffic from client to cache1 to switch s1.")
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
            
            print("--- Migration took %s seconds ---" % (time.time() - start_time))
            log_message("client ping 10.0.0.12 (cache) with 10 packets:")
            ret = client.cmd("ping -c 10 10.0.0.12")
            print(ret)

            time.sleep(3)
            mgr.removeContainer("cache_server_cache2")

            log_message("Starting migration from cache1 to cache2 in 30 seconds...")
            time.sleep(30)
            log_message("Deploy cache service on cache2.")
            start_time = time.time()
            cache_server_cache2 = mgr.addContainer(
                "cache_server_cache2",
                "cache2",
                "davideparpi/nginx-hls-cache",
                ""
            )
            if not AUTOTEST_MODE:
                spawnXtermDocker("cache_server_cache2")

            log_message("Mod the added flow to forward traffic from client to cache2 to switch s1.")
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
            
            print("--- Migration took %s seconds ---" % (time.time() - start_time))
            log_message("client ping 10.0.0.12 (cache) with 10 packets:")
            ret = client.cmd("ping -c 10 10.0.0.12")
            print(ret)

            time.sleep(3)
            mgr.removeContainer("cache_server_cache1")

            restart = 2
            while restart not in range(0,2):
                print("\nDo you want to restart the migration?")
                print("----------------------------\n")
                print("0) restart the migration")
                print("1) stop and go to Mininet CLI\n")
                restart = int(input("Enter your choice: "))
                if(restart not in range(0,2)):
                    print("\nYour choiche is not correct. Retry\n")

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

