# Glossary of my homelab

This is a list of topics/concepts and their corresponding definition and/or contextualization 
that I learned from setting up and running my homelab/server.
Therefore, the notes below focus only on topics important or related to hosting a homelab/server.

The topic that was newer to me was networking:

> [!CAUTION]
> **MISCONFIGURING YOUR NETWORK CAN LEAD TO SECURITY RISKS!!!**

To avoid any security risk, I have **NEVER** enabled port forwarding
and I am able to remotely connect to my home network (using Tailscale, which is free and mostly open source).

> [!NOTE]  
> I am no expert on networking or any of the other topics, 
> thus the notes below may contain incorrect information. 
> If that is the case, please let me know and I will be happy to address the mistakes.


## Networking

### LAN, WAN, ISP, tailnet

Definitions:
- _LAN_ = Local Area Network
- _WAN_ = Wide Area Network
- _ISP_ = Internet Service Provider (e.g. AT&T, T-mobile, Verizon, Vodafone)
- _router_ = a device that forwards data packets to the appropriate parts of a network

In the context of a homelab, there is always a _router_ and an _ISP_.
- When talking about _WAN_, one actually means the _WAN port_ in your router,
which is used to establish a connection with an external network like the internet (via your ISP).
- The _LAN_ corresponds to all the devices connected via WiFi or Ethernet to your router.

If you have a Tailscale account,
- The _tailnet_ corresponds to all the devices connected to your Tailscale account. 

![Alt text](./glossary_media/lan_wan_isp_tailnet.png?raw=true)

Because networks correspond to a set of connected devices, 
_malicious attackers_ inside a network can talk to other devices in the same network and potentially attack/hack them.
- The internet contains malicious attackers (if not, what a wonderful world we would live in...).
- Your LAN does not contain malicious attackers unless "untrusty people" can access it (e.g. a malicious roomate).
For simplicity, we are going to assume your LAN is a trusted network
(there are ways of dealing with this problem).
- Your tailnet does not contain malicious attackers. You can control who has access to it, thus you should only include trusted devices/people.

A _security risk_ would correspond to a malicious attacker being able to access your LAN, 
as it could potentially hack your devices. 
To avoid this, routers only allow _one-way communication_* by default: 
your devices can talk to devices in the internet, but devices in the internet cannot talk to your devices.
This way malicious attackers cannot talk/see the devices in your LAN, and thus they cannot attack them.

The rules for restrictring or permitting the flow of traffic between devices in a network is known as a _firewall_.

![Alt text](./glossary_media/one-way_firewall.png?raw=true)

Wait, so if I ask Google for "dog pictures" when connected to the WiFi, how does Google send me the results if it cannot talk to me?

Actually, the router's firewall does not allow just one-way communication (hence the asterisk from before).
The router's firewall is a _stateful firewall_: 
it remembers what packets it has seen in the past and can use that knowledge when deciding what to do with new packets that show up.
So, if you have asked Google a question, the router knows that you should expect an answer from Google and it will only allow answers for Google during a certain time, 
then it will block again the connection. Therefore, only Google can respond to you and thus malicious attackers still cannot reach your devices.

![Alt text](./glossary_media/stateful_firewall.png?raw=true)
_Here, 2.2.2.2 is your laptop in your LAN, 5.5.5.5 would be "Google", and 7.7.7.7 any "malicious attacker"._
_Image from Tailscale_ [[_ref_]](https://tailscale.com/blog/how-nat-traversal-works).

_Sources: Wikipedia and Tailscale_


### NAT

Before discussing the IP addresses in WAN and LAN, one needs to know about
- _NAT_ = Network Address Translation (also known as _IP maskerading_)

The _Internet Protocol_ (_IP_) specifies how to send data between devices, 
and its most widespread version of the protocol is version 4 (_IPv4_).
One of the things the Internet Protocol standarizes is how to address/identify the devices in the Internet.
Each device in the "Internet network" gets an _IP address_ corresponding to a 32-bit number, 
which uniquely identifyies the device in this network.
There are in total 2^32 ~ 4 billion distinct addresses.
By 1992 (22 years after the creation of IPv4), it became evident that that would not be enough,
leading to an _IPv4 address exhaustion_ problem.

The NAT method originated as a "short-term" solution for this problem.
This technique maps an IP address space into another one 
by modifying the network information in the data packets that are transmitted.
Let's unpack this, focusing on the _one-to-many_ NAT that your router uses.

The common scenario is that your ISP has given you a **single** _public IP address_:
an IP address of the Internet network so that you can talk to and receive data from devices in the Internet network.
Per se, this is not very useful because you would only be able to have 
a single device connected to the Internet network using your public IP address.
The solution is that your router uses your public IP address and talks to the 
internet "on behalf of your LAN devices". 
In a simplistic example, if you ask Google for "cute dogs" with you PC connected to your LAN,
1. the PC is going to tell the router "I want to ask Google for 'cute dogs'"
1. the router is going to use the public IP address to ask Google for "cute dogs"
1. the router is going to receive the data/answer from Google
1. the router is going to send the received data to the PC

The devices in your LAN also use the Internet Protocol to send data between each other (including the router),
and thus they need an IP address used inside the LAN, known as _private IP address_.
The packets (transmitted following the Internet Protocol) have network information that
specify the source and destination of the packet (using IP addresses).
The router (which is implementing NAT) changes the source and destination IP addresses of the packets accordingly before sending them to the Internet:
- Packets passing from the private network to the public network will have their source address modified, 
- Packets passing from the public network back to the private network will have their destination address modified.

![Alt text](./glossary_media/nat_packet_edits.png?raw=true)
_Here, "Host" is your laptop in your LAN, and "Server" would be "Google"._
_Image from Wikipedia_ [[_ref_]](https://en.wikipedia.org/wiki/Network_address_translation).

What happens if your PC asks for "cute dogs" to Google and your laptop asks for "cute cats"?
How does the router know to which device send each of the answers from Google?

To avoid ambiguity in how replies are translated, the packets are modified in other ways.
The two most common protocols to modify the packets are the _Transmission Control Protocol_ (_TCP_)
and the _User Datagram Protocol_ (_UDP_). 
Theses protocols use the _ports_ of your devices (and router):
- A port identifies to which program or service in a device a packet/data should go.
The full description of where a packet should go is: IP address + port.
More information about ports in the section below.

For example, even though Mozilla Firefox and Chrome can be talking to "Google" at the same time,
they use different ports in your device so that the communication is not mixed.

In the TCP and UDP protocols, the port numbers in the packets are also changed so that the combination of IP address + port number
can be unambiguously mapped to the corresponding device + port in the (private) LAN.
This type of NAT is also known as _Network address and port translation_ (_NAPT_).
More information about TCP and UDP can be found below.

Going back to the "standard scenario" mentioned before, it is possible that your ISP hasn't given you a "true" public IP address.
In the case they do not have many available public IP addresses, 
they can run a NAT and give you one of their private IP address as "public IP address". 
Therefore, the packets sent through your devices in your LAN will go through two NATs: your router's and your IPS's.
This "ISP NAT" is known as _Carrier-grade NAT_ (_CGN_ or _CGNAT_) or _large-scale NAT_ (_LSN_).
If you are under a CGN, you can sometimes ask your ISP to give you a "true" public IP address.
There are known disadvantages of CGN to the users.

The private and public network differences explains why it is possible for devices to be connected to the WiFi
(i.e. being connected to your private network) and not have Internet access 
(e.g. a problem is happening with the router and the public IP address).

_Sources: Wikipedia_


### IP address format and ports

### Firewall and `iptables`

### Port forwarding and opening a port

### UPnP

### Linux commands for networking

### NAT transversal

### DNS

### DNS in tailnet

### TCP, UDP

## Server

### Hardware to run 24/7

### SATA connectors and storage

### Mounting disks

### Monitoring sensors

### `systemd` services and timers

### Updates and reboot

## Docker

### Docker containers, images, compose

### Docker vs bare metal

### Configuration of containers

### Networking and disks inside Docker

## Backups and file types

### 3-2-1 rule

### `rsync`

### Organization and file types

