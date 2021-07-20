<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/davideparpinello/VideoFlux">
    <img src="media/logo.png" alt="Logo" width="210"> 
  </a>

  <h3 align="center">VideoFlux</h3>

  <p align="center">
    A service migration framework for live video streaming using SDN and Virtualization
    <br />
    <a href="https://github.com/davideparpinello/VideoFlux/blob/master/media/thesis.pdf"><strong>Download thesis »</strong></a>
    <br />
    <br />
    <a href="https://github.com/davideparpinello">Davide Parpinello</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about">About</a>
    </li>
    <li>
      <a href="#requirements">Requirements</a>
    </li>
    <li>
      <a href="#steps">Steps</a>
    </li>
    <li>
      <a href="#support-and-future-deployment">Support and future deployment</a>
    </li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About

This repository contains the source code for a service migration framework for live video streaming using SDN and Virtualization. The project has been deployed during an internship for University of Trento, under the supervision of Prof. Fabrizio Granelli.

The dissertation of this internship, also presented as thesis for the Bachelor's Degree's final exam, can be downloaded <a href="https://github.com/davideparpinello/VideoFlux/blob/master/media/thesis.pdf">here</a>. The dissertation contains a bit of theory and the complete explanation of the system.

## Requirements

To build this project there are some software requirements:
- <b>ComNetsEmu</b>, an holistic testbed/emulator for SDN and NFV. Installation and configuration is available on the project's <a href="https://git.comnets.net/public-repo/comnetsemu">repo</a>
- <b>Vagrant</b>, required by ComNetsEmu
- <b>Docker</b> (not mandatory) to build Docker images
- <b>An X11 server</b> installed on the host machine. E.g., Xquartz, Xorg.

## Steps

The first step to use this framework is to configure the ComNetsEmu virtual machine, as shown in its repository.

With ComNetsEmu working, first clone this repository locally, then it is necessary to build from scratch (inside ComNetsEmu) or pull the pre-built Docker containers from the Hub.

- <b>Build from scratch</b>: to achieve this is enough to run the build script `build_containers.sh` as superuser. The script will automatically build the three containers needed for the framework. In this case, the Python script `comnetsemu-scripts/topology_simple.py` will need to be modified on rows 144, 151, 161 with the correct containers' names.
- <b>Pull from Docker hub</b>: running the script `pull_docker_containers.sh` as superuser. The script will pull prebuilt containers from Docker hub.

With the containers correctly built or pulled, it is necessary to configure correctly the X11 Forwarding, enabling the test-client image to show VLC or Apache Jmeter on the host screen. To achieve this, is best to disable the access control list on the host machine, using the command `xhost +`, then set the DISPLAY environment variable of ComNetsEmu with the host's IP address using the command `export DISPLAY=192.168.1.2:0`. Change this accordingly to your configuration. This specific configuration is needed because Docker hosts inside ComNetsEmu are not able to forward X11 using only localhost, having a particular network configuration.

With the X11 forwarding setted up, it's possible to start the main Python script with `sudo python3 topology_simple.py`. The script will automatically deploy the containers, set up the network and start three Xterm connected to the different hosts. The script will ask the user when to start with the migration, that will be performed three times with about 30 seconds between each other. At the end, the script will ask the user to perform again the migration or stop and exit.

To test the stream with VLC, it is enough to start it inside the client Xterm with the command `vlc` and open the stream `http://10.0.0.12:8080/hls/stream.m3u8`. If the VLC's GUI will not show up it's necessary to check the correct X11 Forwarding configuration. To use Apache Jmeter, move to the directory `/apache-jmeter-5.3/bin/` and start it with `./jmeter`. A pre-configured project is available in `/apache-jmeter-5.3/bin/hls-graphs.jmx`.

## Support and future deployment

Feel free to ask the author for advices or troubleshooting. Giving the complexity of the system is easy to find issues.

If you have any ideas on how to improve this project please fork it and give credits about the original work.