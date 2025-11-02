# Glossary of my homelab

This is a list of topics/concepts and their corresponding definition and/or contextualization 
that I learned from setting up and running my homelab/server.

The topic that was newer to me was networking:

> [!CAUTION]
> **MISCONFIGURING YOUR NETWORK CAN LEAD TO SECURITY RISKS!!!**

To avoid any security risk, I have never enabled port forwarding
and I am able to remotely connect to my network (using Tailscale, which is free and mostly open source).

> [!NOTE]  
> I am no expert on networking or any of the other topics, 
> thus the notes below may contain incorrect information. 
> If that is the case, please let me know and I will be happy to correct the mistakes.

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


### IP address format and ports

### NAT

### Firewall and `iptables`

### Port forwarding and opening a port

### UPnP

### Linux commands for networking

### NAT transversal

### DNS

### DNS in tailnet

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

