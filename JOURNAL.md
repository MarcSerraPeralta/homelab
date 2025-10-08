# 2025/10/06 - Setting up new home server (Part 1)

I just bought a HP Elitedesk 800 G1 USDT (for 50.00€) with the following specs:
```
Operating system: Windows 10 Pro
Processor Intel(R) Core(TM) i5-4590S CPU @ 3.00GHz 
Installed RAM 4+4 GB (1600 MT/s)
Storage 224 GB SSD KINGSTON SUV400S37240G
Graphics card Intel(R) HD Graphics 4600 (113 MB)
```
which included Power Cable + Original HP AC Adapter + HP mouse.
The reason for using a mini PC as a home server is explained in issue [#3](https://github.com/MarcSerraPeralta/homelab/issues/3).
I have chosen this specific mini PC because it is cheap and the CPU has a "high" frequency (see [hardware recommendations for Tailscale](https://tailscale.com/kb/1320/performance-best-practices#machine-sizing-recommendations)) and 4 cores.

The system boots up and Windows runs correctly. 
I am using the Displayport to connect to my display and an ethernet cable for Internet.

The first thing I will do is install Ubuntu Server 24.04 LTS because:
- the OS uses little resources (does not have GUI)
- it has Long-Term Support (LTS)
- it is very stable and has a big community (helpful for debugging and support)
- I have daily run a Linux Mint machine (so I am comfortable with Linux)
- Tailscale and pi-hole can be easily installed
- Tailscale recommends having a Linux kernel version 6.2 or above ([Tailscale docs](https://tailscale.com/kb/1320/performance-best-practices#operating-system-recommendations)) and this OS has version 6.8 ([Ubuntu docs](https://ubuntu.com/download/server))

It can be tricky to boot the Elitedesk from a USB (see tricks in [this reddit post](https://www.reddit.com/r/homelab/comments/r1hhhz/issues_with_booting_hp_elitedesk_800_g2_mini_from/)).
I have a 16GB USB 2.0 stick and the Elitedesk BIOS version is 2.15.1236 (from 2014 if I am not mistaken). 
I am following these steps to install Ubuntu Server:
1. Burn the USB stick with the Ubuntu Server 24.04 LTS ISO. 
1. Plug the USB stick in a USB 2.0 port of the Elitedesk (a non-blue port).
1. Start the Elitedesk and start smashing the `Esc` key to enter the BIOS menu.
1. Once in the BIOS, select `Computer Setup (F10)`. 
1. Go to `Storage` > `Boot Order`, and then move the `USB Hard Drive` to the top.
1. Save the changes (`File` > `Save Changes and Exit`). The PC will automatically restart.
1. Once the PC is back on, select the option `Try and Install Ubuntu Server`.
1. It will take quite some time to set up Ubuntu Server and start the installation guide.
1. Go over the installation steps.
    1. The network configuration is more tricky than I expected. Because I dont have time now, I have cancelled the installation and will continue another day.

# 2025/10/07 - Setting up new home server (Part 2)

I have done some research about the network configuration. 
I will set both IPv4 and IPv6 to automatic (DHCP = Dynamic Host Configuration Protocol), which means that the router assigns a random IP address whenever the router or the PC/server gets rebooted. 
I can always set up a static IP address for the server later on (this can be done at the server side or at the router side). 

Continuing with the Ubuntu Server installation:
1. Base for the installation = Ubuntu Server
1. Network configuration = eno1 with IPv4 automatic (DHCP) and IPv6 automatic (DHCP)
1. Proxy address = (leave blank)
1. Mirror address = (I left the default one)
1. Storage configuration = "Use entire disk" and "Set up this disk as an LVM group" (selected as default). 
The LVM is a Logical Volume Manager which makes it easier to resize partitions and add new disks.
In the summary page of the storage configuration, I see that only 100GB (out of the 235GB available),
are used as a Logical Volume (mounted at `/`) while the other 135GB are not allocated.
As it will be easy to resize partitions (because of LVM), I will leave the LV as is. 
1. Ubuntu Pro = (I left it as not selected)
1. SSH configuration = Select "Install OpenSSH server" (so that I can SSH into the server)
1. Featured server snaps = (leave all of them unchecked)

After this, the installation has started (it only took a couple of minutes).
Then, I reboot the PC (it asks me to remove the USB stick and then press `Enter`). 
The PC has rebooted without issues. I log in with my new username (specified in the `myserver login:` field) and my new password.

Fist thing is to check that my server is connected to the internet:
```
ip a
```
which returns me an IP address for `eno1`. Also,
```
ping -c 3 8.8.8.8
ping -c 3 google.com
```
(8.8.8.8 is one of Google’s public DNS servers, always online and reliable)
I have an average round-trip time for `google.com` of ~4ms, which is good.

Second thing to do is to update the system:
```
sudo apt update
sudo apt upgrade
sudo apt autoremove
```

Now I can test the internet bandwidth, I have installed `speedtest-cli` and run its test:
```
sudo apt install speedtest-cli
speedtest-cli --secure
```
I get the following performance (connected via Ethernet cable):
```
Hosted by ... [176.88 km]: 8.658 ms
Download: 89.36 Mbit/s
Upload: 95.25 Mbit/s
```
which is more or less what I see in my laptop when connected via Ethernet.

Next is to set up a static IP address to reliable access this server via Tailscale.
For that, I am going to do a DHCP reservation in my router (so that my server always get assigned the same IP).
Once done, if I run `ip a` I get the reserved IP address, so it works.
I have rerun the tests to check the internet speed. 

I have SSHed to my server in my laptop using
```
<myserver-username>@<myserver-ip>
```
I would like to be able to access to my server from all devices using its hostname (instead of its IP).
However, my TP-Link router does not seem to allow for adding local DNS entries.

Last thing I have done before installing tailscale is check that the timezone is correct:
```
timedatectl
```
It has an incorrect timezone, so I have set it to the correct one 
```
timedatectl set-timezone Europe/Amsterdam
```
(use `timedatectl list-timezones` to get a list of all possible timezones).

### Installing Tailscale as VPN

The motivation for using Tailscale as a VPN is described in [#2](https://github.com/MarcSerraPeralta/homelab/issues/2).

First, I have created a Tailscale account. 
It has asked me to add my first device by running
```
curl -fsSL https://tailscale.com/install.sh | sh
```
on my server. Then, I also need to run (on my server)
```
sudo tailscale up
```
which prints an HTTPS link that I had to type in my laptop to set up `myserver` in Tailscale.
Now, Tailscale asks me to add a second device, so I will add my laptop.
Then, Tailscale asks me to ping `myserver` from my laptop, which I can do (with latency of ~3ms).
- I have also installed Tailscale in my phone and I can ping it from my laptop when the phone is not connected to the Wifi.
In that case the latency is not very stable: `rtt min/avg/max/mdev = 21.712/126.004/315.921/87.585 ms` (40 packets).
- I have also SSHed to `myserver` from my laptop using the Tailscale IP for the server.
- I have also SSHed to `myserver` from my laptop using the Tailscale hostname for the server.

Next thing I did was disabling key expiry for `myserver`.
I have also disabled UPnP in my router, as recommended by Tailscale and other sources in the internet.
I have also checked that I do not have any open ports (they are listed in `Forwarding > Virtual Servers`).

Finally (for now), I will set `myserver` as an exit node, so that all my web traffic can go through my home internet (if I am not at home).
```
sudo tailscale down
sudo tailscale up --advertise-exit-node
```
The command also prints a warning:
```
Warning: UDP GRO forwarding is suboptimally configured on eno1, UDP forwarding throughput capability will increase with a configuration change.
See https://tailscale.com/s/ethtool-config-udp-gro
```
I followed the guide in the website, which corresponds to test
```
systemctl is-enabled networkd-dispatcher
```
which should output `enabled`. Then, run the following commands:
```
printf '#!/bin/sh\n\nethtool -K %s rx-udp-gro-forwarding on rx-gro-list off \n' "$(ip -o route get 8.8.8.8 | cut -f 5 -d " ")" | sudo tee /etc/networkd-dispatcher/routable.d/50-tailscale
sudo chmod 755 /etc/networkd-dispatcher/routable.d/50-tailscale
```
and test that it worked:
```
sudo /etc/networkd-dispatcher/routable.d/50-tailscale
test $? -eq 0 || echo 'An error occurred.'
```
which worked. I repeated the commands to set Tailscale down and back up as an exit node, and now I get the following warning:
```
Warning: IP forwarding is disabled, subnet routing/exit nodes will not work.
See https://tailscale.com/s/ip-forwarding
```
The guide that I will be following is [https://tailscale.com/kb/1103/exit-nodes](https://tailscale.com/kb/1103/exit-nodes), which seems more appropiate to set up exit nodes.
OK, so the exit-node guide refer to the one in the warning about the IP forwarding.

I have checked that my server has `ufw` (Uncomplicated Firewall) but it is disabled.
The default `ufw` rules (in `/etc/default/ufw`) are: deny incoming, accept outgoing, disable routed.
The Tailscale website from the warning says "ensure your firewall denies traffic forwarding by default".
To also avoid locking myself out via SSH, I run these two commands:
```
sudo ufw default deny routed
sudo ufw allow ssh
```
Checking `/etc/default/ufw` and `sudo ufw status verbose`, I see that the rules+defaults have been updated.
So, I activated the `ufw` with
```
sudo ufw enable
```
After finishing the instructions from the guide, running
```
sudo tailscale down
sudo tailscale up --advertise-exit-node
```
does not show any warning. 

Finally, I went to the admin console of Tailscale, opened the Machines page, and allowed `myserver` to be an exit node.
Using my phone, I checked that I can connect to the exit node of my server (with Wifi disabled).

Final comment, I have tried SSHing to `myserver` when UFW denies SSH and it still works from my laptop, so I am just going to keep SSH denied.
I have also rebooted the server to check that all the configuration has not changed and that the exit node still works.


# 2025/10/08 - Bechmarking home server and solving bugs

I wanted to benchmark the exit node by running some speed tests on my smartphone.
The results of speedtest.net for bandwidth and ping are:
```
WiFi: 81.39 Mbps and 9 ms
data: 80.82 Mbps and 14 ms
data + connected to tailnet: 81.25 Mbps and 20 ms
data + connected to my server (exit node): 79.74 Mbps and 26 ms
```
(I was connected to the same server for all the tests)

During this benchmark I have seen some issues that need to be solved:
- Keyboard does not work if plugged after the server is turned on. 
However, it works if it is connected before turning on the server.
- Tailscale is not up by default after reboot (+ user log in).

I have created two issues in GitHub to keep track of the problems that need to be solved.
