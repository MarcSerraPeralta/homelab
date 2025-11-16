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


### IP addresses, ports, subnets

Definitions:
- IP address = identifies the device in a network. 
- Port = identifies the program or service in a device talking to the network. 

Therefore, the complete information of the source and destination of the packets is given by IP address + port.
For example if the browser in your laptop asks for "cute dogs" to Google, the source IP address is:
`{laptop's IP address}:{browser's port}`.

For IPv4, the IP address is a number of 32 bits: between 0 and 2^32 - 1.
For IPv6, the IP address is a number of 128 bits.
All devices have 65535 ports (almost 16 bits), so a port is always a number between 0 and 65534.

For IPv4, the IP address is usually written as `{8-bit number}.{8-bit number}.{8-bit number}.{8-bit number}.`.
An 8-bit number goes from 0 to 255.
A valid IPv4 address is `192.0.1.120` or `2.2.2.2`.

For IPv6, the IP address is written as 
`{4 hex}:{4 hex}:{4 hex}:{4 hex}:{4 hex}:{4 hex}:{4 hex}:{4 hex}`,
that is: eight groups of four hexadecimal digits each, separated by colons.
The IP address can be shortened, with `0000:0000` being replaced by `:`.
For example, `2001:0db8:0000:0000:0000:8a2e:0370:7334` 
becomes `2001:db8::8a2e:370:7334`.

There are some special IP addresses which arise from the use of _subnets_:
- subnet = a logical subdivision of an IP network, 
which corresponds to a set of nodes/devices in the network.

The default modern way of specifying a subnet is by a _CIDR block_.
For now, knowning what a _CIDR block_ is is not important (see definition in the section below),
we only need how it is represented and written down.

In CIDR notation, a CIDR block is specified with `{IP address}/{number}`, with the number going from 0 to 32.
The IP addresses of the devices in the CIDR block have the same first `number` bits (from left to right) as the given IP address.
This prefix for the subnet is known as the _network prefix_.
For example, `122.50.111.15/24` means that the devices in the CIDR block have IP addresses of the form
`122.50.111.x` (with `x` any number between 0 and 255), as `3*8 = 24`.
The rest of the IP address is the _host identifier_,
which specifes a particular device on that network.
The number of devices in a particular CIDR block for IPv4 is therefore `2^(32 - number)`.

The special IPv4 addresses and CIDR blocks are:
- `0.0.0.0` = "All interfaces". 
It is used to mean "listen to all interfaces/networks" when sending and receiving packets.
- `127.0.0.0/8` = refers to the same/self device, thus packets never leave the device.
- `127.0.0.1` = `localhost`, useful for testing or running services locally on a device.
- `192.168.0.0/16` and `172.16.0.0/12` = private networks.
- `255.255.255.255` = "Broadcast". It is used to mean "send a message to all devices on the network".

There are also special port numbers:
- 80 = HTTP
- 443 = HTTPS
- 22 = SSH
- 20-21 = File Transfer Protocol (FTP)
- 53 = Domain Name System (DNS)
- 67-68 = Dynamic IP assignment (DHCP)
- 25 = SMTP (for sending email)
- 110 = POP3 (for receiving email)
- 143 = IMAP (for receiving email)

It is possible to specify which programs/services are able to listen/use each port.
For the case of Linux-based devices, the kernel is responsible for that.
One can check what is listening to which ports using:
```
sudo netstat -tulpen
```
which returns
```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       User       Inode      PID/Program name    
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      101        24760      930/systemd-resolve 
tcp        0      0 0.0.0.0:36407           0.0.0.0:*               LISTEN      1000       52460      5542/deno           
tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN      0          32887      1251/cupsd          
tcp        0      0 100.90.224.7:37947      0.0.0.0:*               LISTEN      0          30344      1107/tailscaled     
tcp6       0      0 ::1:631                 :::*                    LISTEN      0          32886      1251/cupsd          
tcp6       0      0 :::80                   :::*                    LISTEN      0          28883      1189/apache2        
tcp6       0      0 fd7a:115c:a1e0::7:45441 :::*                    LISTEN      0          30346      1107/tailscaled     
udp        0      0 0.0.0.0:47367           0.0.0.0:*                           122        32839      988/avahi-daemon: r 
udp        0      0 127.0.0.53:53           0.0.0.0:*                           101        24759      930/systemd-resolve 
udp        0      0 0.0.0.0:41641           0.0.0.0:*                           0          25170      1107/tailscaled     
udp        0      0 0.0.0.0:5353            0.0.0.0:*                           122        32837      988/avahi-daemon: r 
udp6       0      0 :::55330                :::*                                122        32840      988/avahi-daemon: r 
udp6       0      0 :::41641                :::*                                0          25169      1107/tailscaled     
udp6       0      0 :::5353                 :::*                                122        32838      988/avahi-daemon: r
```

_Sources: Wikipedia_


### DHCP, static and dynamic IP addresses

Definitions:
- _Dynamic Host Configuration Protocol_ (_DHCP_) = network management protocol used on Internet Protocol networks 
for automatically assigning IP addresses (and other parameters) to devices in the network.
- _DCHP server_ = component/device in a network that assigns IP addresses following the DHCP.

The role of the DHCP is to avoid devices self assigning an IP address which can lead to conflicts,
i.e. two devices with the same IP address inside the same network.

In the home LAN, the DHCP server is the router.
The IP assignments may be _static_ (fixed or permanent) or _dynamic_.
The dynamic ones change every time the device is connected to the network
and can also change every a certain number of hours.
By default, the IP assignments are dynamic.
Static IP addresses are only required for e.g. servers, printers, routers...

Static IP addresses can be set up thank to the _MAC address_ present in all devices:
- _Medium Access Control address_ (_MAC address_) = unique identifier "burned in" in any device that can connect to a network.

Therefore, MAC addresses can be used as a device indentifier in networks and allow for being able to assign the same IP address to a device every time it connects to the network.

The general steps to assign an IP address to a device are:
1. DISCOVER: the device/client (without an IP address) broadcasts a message to search for a DHCP server to `255.255.255.255`.
The message includes the _MAC address_ of the device.
2. OFFER: the DHCP server receives the message and reserves an IP address for the device
(identified by the MAC address). It then sends a message to the device with the reserved IP address.
3. REQUEST: the device requests the offered address to the DHCP server. 
This is done because the device can receive DHCP offers from multiple servers, but it will accept only one of them. 
4. ACKNOWLEDGEMENT: the DHCP server sends the lease duration and any other information that the device requested.

In home routers, one can specify the range of dynamic IP addresses that can be offered in the DHCP, as well as the range of static IP addresses.
It is important that the two ranges do not overlap, so that e.g.
the static address of device A (which is currently not connected to the network, thus the IP address is not used) 
is not given as a dynamic address to device B. Then, if device A connects to the network, there is a conflict of IP addresses.

_Source: Wikipedia_


### Firewall and `iptables`

### Port forwarding and opening a port

### UPnP

### Linux commands for networking

- list programs/services and the port they are listening to:
```
sudo netstat -tulpen
```
```
sudo ss -tulpen
```
- routing table:
```
ip route show
```
see section _IP routing, routing tables, CIDR_ for more information of the output.


### NAT transversal

### DNS

Definition:
- _Domain Name System_ (_DNS_) _server_ or _resolver_ = translates/maps/resolves domain names to IP addresses.
- _Domain name_ = unique human-readable address to identify web servers (e.g. `example.com`).
- _Uniform Resource Locator_ (_URL_) = web address containing the domain name of a site as well as other information, 
including the protocol and the path.
For example, in the URL `https://cloudflare.com/learning/`:
`cloudflare.com` is the domain name, `https` is the protocol, and `/learning/` is the path to a specific page on the website.
- _Hostname_ = identifier (string) that is assigned to a device connected to a network.
It can be a domain name if it has been appended to a DNS.

The DNS server is only used by the devices in a network to get the IP addresses of domain names.
This means that the DNS does not handle web traffic itself, it is just a "lookup table".
The devices talk to port 53 (reserved for DNS requests) of the DNS server using the TCP and UDP protocols
(see _NAT_ section and _TCP, UDP_ section for more informaiton).

A _DNS record_ is an pair/map of IP address and domain name.
If the address is IPv4, the record type is `A`; while if the address is IPv6, the record type is `AAAA`.

When setting up a home DNS server, it will not store all the possible mappings of IP addresses and domain names.
The home DNS server will end up asking DNS servers in the internet that actually hold the DNS records (known _as authoritative DNS servers_).
The type of DNS server that asks to other DNS servers is known as _recursive DNS server_.

![Alt text](./glossary_media/dns_record_request_sequence_recursive_resolver.png?raw=true)
![Alt text](./glossary_media/dns_hierarchy.png?raw=true)
_Images from [Cloudflare learning](https://www.cloudflare.com/learning/dns/what-is-dns/)._

It is important that the home DNS server is not its own DNS root nameserver, 
to avoid getting stuck in an infinite loop where the home DNS server just continues asking itself "What is the IP address of `google.com`?".
To solve this, one can just specify the DNS root nameserver of the home DNS server to be e.g. the one from Google or Cloudflare.

_Source: Wikipedia and Cloudflare learning_


### Web servers

Definition:
- _Web server_ = stores website files and sends them to the users.

Web servers listen to HTTP and HTTPS requests and then:
- returns the appropiate HTML files = _static file serving_

or
- passes requests to applications (e.g. Go, Python) = _application hosting_

Usually, web servers sit behind a reverse proxy for several advantages (see _Reverse proxies_ section).

_Source: Wikipedia and Cloudflare learning_


### Reverse proxies

Definition:
- _Reverse proxy_ = server that sits in front of web servers and
and forwards clients requests to the appropiate services of those servers.

![Alt text](./glossary_media/reverse_proxy.png?raw=true)

Reverse proxies are used for increased security, load balancing, routing, filtering, reliability...
They can handle HTTP, HTTPS, TCP... protocols 
and forward client requests to specific ports of web servers.
In particular, the steps involved in forwarding client requests inside a reverse proxy are the following:
1. Accepts a web request from a client
1. Decides which (backend) service (defined by `IP:port`) should handle it
1. Sends the request there
1. Returns the response to the client

Usually, the IP returned by the DNS is a reverse proxy that handles everything.
As an example, if the client searches for `example.com/blog`:
1. DNS returns the IP address associated with `example.com` (here we assume this IP address is a reverse proxy)
1. the `/blog` web request is sent to the reverse proxy
1. the reverse proxy asks to the "blogs" service (which has an associated `IP:port`)
1. the reverse proxy sends the answer to the client

_Source: Wikipedia and Cloudflare learning_


### TCP, UDP

### IP routing, routing tables, CIDR

Definition:
- IP routing = the process of deciding which path the packets should take through the network.

As mentioned before, the packets contain a source IP address and a destination one.
Routers need to forward the packets to the correct destination.
Note that a packet can jump/hop through several routers until reaching its destination.
Routers have a _routing table_ to perform IP routing:
- Routing table = a lookup table to know where to send/forward the packets, e.g. "if the packet destination is X, send it to Y".

Routers look at each packet’s destination IP address and forward it toward its next hop, 
step by step, until it reaches the target device.
Instead of listing every IP address in the routing table, routers use _CIDR blocks_
to represent a group of addresses that share the same route.
This reduces the storage used by the routing table and also allows routers to make decisions more efficiently.
- _Classless Inter-Domain Routing_ (_CIDR_) = method for allocating IP addresses for IP routing.
- _CIDR block_ = set of IP addresses that share the same IP route.

To get the routing table in a Linux device, run:
```
ip route show
```
which returns something like
```
default via 192.168.0.1 dev eno1 proto dhcp src 192.168.0.42 metric 100 
192.168.0.0/24 dev eno1 proto kernel scope link src 192.168.0.42 
```
which means
- `default` = `0.0.0.0/0` = everything
- after `via` specifies where to send the packets
- after `dev` specifies which interface to use
- after `proto` specifies who added this line in the routing table
- `scope link` = only valid for IP addresses reachable on this link/device (no `via`)
- after `src` specifies which source IP to use when sending the packets
- after `metric` specifies the priority of this rule in case multiple rules apply (lower = more priority)

Then, the output shown above means:
- Send all traffic not matching a more specific rule to `192.168.0.1` (the router) via `eno1` using `192.168.0.42` as source for the packets.
- For any traffic to `192.168.0.x` addresses, send it directly through `eno1` using `192.168.0.42` as source for the packets.

_Sources: Wikipedia_


## Server

### Hardware to run 24/7

### SATA connectors and storage

### Mounting disks

### Monitoring sensors

### `systemd` services and timers

### Updates and reboot

### Software

#### Caddy

Web server that is very easy to configure and that has lots of features:

- reverse proxy
```
example.com {
    reverse_proxy IP:port
}
```
- static file server (web server)
```
example.com {
    root * /path/to/html/files
    file_server
}
```
- URL rewriting
```
example.com {
    @root path /
    rewrite @root /admin
```
_when the request's path is `/`, rewrite it internally to `/admin`. 
The URL stays `/` (no redirect)_
- TLS certificates (own CA handled automatically)
```
example.com {
    tls internal
}
```

#### Pihole (v6)

Pihole is a DNS that blocks ads by not returning the IP if the hostname is in an "ad list".
Therefore, it blocks (almost) all ads network wise.
It has a web interface to monitor and configure everything.

Pihole v6 has the web interface and the REST API embedded directly into `pihole-FTL` (which handles the DNS requests),
thus it does not depend on `lighttpd` nor `PHP`. It has native HTTPS support.
The configuration is done using the `pihole.toml` file.

The DNS uses port 53 (cannot be changed) and the web interface uses ports 80 and 443 (these can be changed).
If one wants to use a reverse proxy in the same machine that runs pihole, then the reverse proxy should use port 80 and 443
(to listen to all HTTP and HTTPS requests) and pihole's web interface should be moved to other ports 
(because pihole and the reverse proxy cannot use the same ports).
These new ports can then be mapped by the reverse proxy to e.g. `pihole.home`.

![Alt text](./glossary_media/pihole_and_reverse-proxy.png?raw=true)


## Docker

### Docker containers, images, compose

### Docker vs bare metal

### Configuration of containers

### Networking and disks inside Docker

## Backups and file types

### 3-2-1 rule

### `rsync`

### Organization and file types

