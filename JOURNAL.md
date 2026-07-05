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
    1. The network configuration is more tricky than I expected. Because I dont have time now, 
    I have cancelled the installation and will continue another day.

# 2025/10/07 - Setting up new home server (Part 2)

I have done some research about the network configuration. 
I will set both IPv4 and IPv6 to automatic (DHCP = Dynamic Host Configuration Protocol), 
which means that the router assigns a random IP address whenever the router or the PC/server gets rebooted. 
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
The PC has rebooted without issues. I log in with my new username (specified in the `myserver login:` field) 
and my new password.

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

Finally (for now), I will set `myserver` as an exit node, so that all my web traffic can go through my home internet 
(if I am not at home).
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
which worked. 
I repeated the commands to set Tailscale down and back up as an exit node, and now I get the following warning:
```
Warning: IP forwarding is disabled, subnet routing/exit nodes will not work.
See https://tailscale.com/s/ip-forwarding
```
The guide that I will be following is [https://tailscale.com/kb/1103/exit-nodes](https://tailscale.com/kb/1103/exit-nodes), 
which seems more appropiate to set up exit nodes.
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

Final comment, I have tried SSHing to `myserver` when UFW denies SSH and it still works from my laptop, 
so I am just going to keep SSH denied.
I have also rebooted the server to check that all the configuration has not changed and that the exit node still works.


# 2025/10/08 - Bechmarking home server and solving bugs

I wanted to benchmark the exit node by running some speed tests on my smartphone.
The results of speedtest.net in my phone for bandwidth and ping are:
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

I have also done some extra benchmarks using laptop on my unversity's internet:
```
(download, upload, ping)
Ethernet: 181.38 Mbps, 152.97Mbps, 8ms
Ehternet + connected to my server (exit node): 85.59 Mbps, 52.28 Mbps, 16ms
```
so it seems that the exit node / my server is limited by the internet speed at my home, which is (on my laptop)
```
(download, upload, ping)
via Ethernet: 93.58 Mbps, 94.05 Mbps, 7ms
via WiFi: 67.90 Mbps, 90.85 Mbps, 21ms
```
(obvously my Elitedesk PC is connected via ethernet).

In the meantime, I will start installing pi-hole following [its guide](https://docs.pi-hole.net/main/basic-install/).
Before the installation, I will set up Tailscale in the server using:
```
sudo tailscale down
sudo tailscale up --accept-dns=false
```
following the steps in [this post](https://fullmetalbrackets.com/blog/pihole-anywhere-tailscale/#set-up-tailscale).
The reason for doing that is because our server will now also act as a DNS resolver 
for both the tailnet and the local network (because it will have pi-hole in it).
The flag is to avoid a 'recursive loop' (more info in the [Tailscale docs](https://tailscale.com/kb/1072/client-preferences#use-tailscale-dns-settings)),
which I will explain now.
First note that the device with the pi-hole acts as both a DNS server for clients and a DNS client 
(e.g. when searching `google.com` inside the device or doing `apt update`).
The recursion occurs when the device acts as a client, because when it tries to ask 
"What is the IP of `google.com`" to the DNS resolver it is basically asking itself 
"What is the IP og `google.com`" because it is the DNS resolver. 
This ends in a recursion loop. 
This happens in both the tailnet and local network as each one has their own different DNS resolver. 

For the local network, this can be solved by setting the resolver of the device hosting pi-hole 
to an external DNS like 8.8.8.8 (Google). 
Then, device knows that if it needs to act as a DNS client, it should look at the external DNS.

For the tailnet, one also needs to use the flag `--assign-dns=false` to ensure Tailscale 
doesn’t overwrite the DNS settings of the device with pi-hole from the previous paragraph 
with the device's own IP (leading to the mentioned recursion).

Therefore, 
- before installing pi-hole into my server, 
I will turn off tailnet so that first I only have to deal with the local network.
- while installing pi-hole into my server, 
I need to make sure to make sure to set up an external DNS (this is to avoid the recursion in my local network)
- after installing pi-hole into my server, 
I need to turn on tailscale with `--assign-dns=false` (to avoid the recursion in my tailnet)

# 2025/10/09 - Installing Pi-hole

Now that I know what is the correct way of setting up the pi-hole (see notes from 2025/10/08), 
I will install pi-hole on my server.
First, I made sure that Tailscale was down:
```
sudo tailscale down
sudo tailscale status
```
As a side comment, Tailscale was up when I booted the server, so I am going to close the corresponding GitHub issue 
(maybe last time I had it down before reboot so it stayed down).
The issue about the keyboard still persists.

Then, I followed the guide from the [pi-hole docs](https://docs.pi-hole.net/main/basic-install/).
- During the installation, it tells me to make sure that the server has a static IP address, which does.
- It also asks me to choose and interface: `eno1` or `tailscale0`. 
I choose `eno1` (which is the local network) because I can then configure Tailscale to use my server as DNS.
- For the upstream DNS provider, I chose `Cloudflare` because it does not store as much log info as Google.
- I included StevenBlack's unified hosts list.
- Regarding query logging, I have enabled it to check that everything works fine at the beginning, 
but I will most likely disable it afterwards.
- I have also selected `Show everything` as privacy mode for FTL to check that everything works, 
but then I will turn it down to `Hide domains and clients` or `Anonymous mode`.

To check that the installation has been successful, I check that pi-hole is active:
```
pihole status
pihole version
```
(my pi-hole core version is v6.1.4, web version v6.2.1 and FTL version v6.2.3).
Just to make sure everything is up to date:
```
sudo pihole -up
```

Next, I wanted to check the Web UI using the HTTP link and password prompted after the installation.
However, the HTTP link gets a timeout error in my laptop.
Researching on the internet, I found  [this forum discussion](https://discourse.pi-hole.net/t/upgrading-to-v6-pihole-up-didnt-disable-lighttpd/76307) and [this other one](https://discourse.pi-hole.net/t/pihole-appears-to-be-working-but-i-cant-access-the-web-interface/61226/4).
- I rebooted my server but the Web UI is still not working. 
- I have installed `lighttpd` using
```
sudo apt install lighttpd
```
The problem is that lightpad cannot start correctly because pi-hole is using port 80.
```
sudo journalctl -u lighttpd --no-pager | tail -20
sudo ss -tlnp | grep :80
```
Therefore, I need to stop the pi-hole, start lighttpd, and then start pi-hole again:
```
sudo systemctl stop pihole-FTL
sudo systemctl restart lighttpd
sudo systemctl status lighttpd
sudo systemctl start pihole-FTL
sudo systemctl status pihole-FTL
sudo systemctl status lighttpd
sudo pihole -r
sudo systemctl restart lighttpd
sudo systemctl restart pihole-FTL
```
So, this didn't work out.
- I have uninstalled pi-hole and set the DNS provider to Cloudflare
```
sudo pihole uninstall
sudo vim /etc/resolv.conf # edit the nameserver line and set it to 1.1.1.1
```

I will now install again pi-hole. First, I make sure that lighttpd is properly running:
```
sudo systemctl restart lighttpd
sudo systemctl status lighttpd
```
Then, I checked that for the pi-hole requirements, I need to have the following
```
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 53/tcp
ufw allow 53/udp
ufw allow 67/tcp
ufw allow 67/udp
ufw allow 123/udp
```
which I didn't (`sudo ufw status verbose`).
I have installed pi-hole with sudo:
```
curl -sSL https://install.pi-hole.net | sudo bash
```
Now, when I try to go to the provided website, I don't get a timeout error, I get a "403 Forbidden Error".
The problem is that lighttpd is using port 80 so pihole cannot use it (`sudo ss -tulnp`).
I just disabled lighttpd and restarted pihole-FTL:
```
sudo systemctl stop lighttpd
sudo systemctl disable lighttpd
sudo systemctl restart pihole-FTL
sudo systemctl status pihole-FTL
```
Now the pi-hole Web UI works!!

What I believe the actual problem was:
- I did not look at the prerequisites and didn't have the correct ufw setup
- maybe I required to do `sudo bash` when installing Pi-hole

I will not uninstall lighttpd, I will just keep it disabled.

First thing now to do is to change the pi-hole password:
```
sudo pihole setpassword
```

Now I will have to configure my networks to use the Pi-hole as their DNS server (see [pi-hole docs](https://docs.pi-hole.net/main/post-install/)).
As a comment, the installation said that I have not configured Pi-hole for IPv6 (only IPv4).

For the local network, I just went to the router settings and changed the DNS to the IP of the server.
I had to reboot (not reset) the router to apply the changes.

For the Tailnet, in my server, I run
```
sudo tailscale up --assign-dns=false --advertise-exit-node
```
To check that there is no recursion loop, I run:
```
ping google.com
```
which works.
Then, to configure the Tailnet DNS, I follow the guide in [this Tailscale post](https://tailscale.com/kb/1114/pi-hole#step-4-set-raspberry-pi-as-the-dns-server-for-your-tailnet).
There is one important thing to do so that pi-hole can be the DNS for tailnet: 
one needs to select "Permit all origins" so that requests from the tailnet are also answered.
By default, pi-hole only listens to local requests (i.e. from the local network), 
but we also want it to answer requests from the tailnet.
This can be done in the Web UI or in the terminal by editing `/etc/pihole/pihole.toml` and 
changing `listeningMode = "LOCAL` to `listeningMode = "ALL"` (not that his varies dependning on the pi-hole version).
Then, one needs to restart pi-hole:
```
sudo systemctl restart pihole-FTL
sudo systemctl status pihole-FTL
```
In my laptop, I run
```
sudo tailscale up --exit-node=
```
and checked that I can do e.g. `ping google.com`.

Finally, I have added the following ad-list to pi-hole:
```
https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.txt
```
see GitHub issue [#10](https://github.com/MarcSerraPeralta/homelab/issues/10) for explaination.
Remeber to run `sudo pihole -g` after updating the ad lists.


# 2025/10/10 - Small changes to pi-hole settings

I have changed the logging settings of the pi-hole.
In the pi-hole web UI, go to Settings > Privacy. 
Select "Expert mode" (click on the "Basic" toggle) and set the Query Anonymization to 
"Hide domains: Display and store all domains as hidden".
This means that the domains are not stored and cannot be seen, which improves the privacy. 

By default, pi-hole only stores the logs for up to 91 days (see `maxDBdays` in `/etc/pihole/pihole.toml`), 
which is good for storage purposes.
I will leave it like this.


# 2025/10/11 - Shut down home server

I have shut down the home server because I want to clean the fans (it is a little bit noisy and bothers me).
After shutting it down, I have changed the DNS prover in the router settings to the default one (not my home server's IP).
Also, if the internet does not work for some devices, make sure that they are not connected to the tailnet.
Recall that the DNS provider for the tailnet is the home server (which is now turned off).
I could change it to the default one, but what is the point of using the tailnet if I don't have my home server turned on.
I have also made the router use only WPA2 for wireless security (before it was using both WPA2 and WPA, which is not super secure).

I have also tested the tailnet's internet speed between two countries (Spain - Netherlands) and I obtained ~80 Mbps.
The bandwidth of my spanish WiFi is 600 Mbps and the cause of the tailnet bandwidth being 80 Mbps 
is that my dutch internet speed is 80 Mbps.


# 2025/10/12 - Share my server with other people

I have shared my server (which I turned on) with my girlfriend so that she can also block the ads with pi-hole. 
This can be done following the instructions in the [Tailscale docs](https://tailscale.com/kb/1084/sharing). 
Note that "sharing" is not the same as inviting someone to your whole tailnet; 
here I am just making my server available to my girlfriend's tailnet. 
For example, she cannot see my phone or my laptop when they are connected to my tailnet. 
After configuring her tailnet to use my server as DNS provider, she can have an (almost-)free-ad experience in her phone. 


# 2025/10/16 - Setting a subnet router to see local IP addresses/websites

I am setting up the subnet router described in issue [#11](https://github.com/MarcSerraPeralta/homelab/issues/11) 
in order to be able to see my router in the tailnet and access it remotely.
I am following the instructions in the [tailscale docs](https://tailscale.com/kb/1019/subnets#set-up-a-subnet-router).
Regarding the IP forwarding, I already set up that in 2025/10/07. 
Note that this IP forwarding in Tailscale is not the same a "port forwarding" in a router (which can be a big security risk).
My router can be locally accessed in the following website: `http://192.168.0.1/`, 
so I will run the usual `sudo tailscale up` with this extra flag:
```
--advertise-routes=192.168.0.0/24
```
Note that the last IP digit is a `0` (not a `1`) because I need to pass it a valid network address, not the host address.
The IP address `192.168.0.0` means "Route all traffic destined for 192.168.0.x through me (the subnet router)".
As stated in the guide, remember to set up the subnet routes through the Tailscale Admin Console (website).

In order to see the my router's webpage, I need to restart my Tailscale connection and pass it this extra argument:
```
--accept-routes=true
```
Then, I can run the following
```
ping 192.168.0.1
```
which runs correctly and I can also visit `http://192.168.0.1/`. 


# 2025/10/21 - Bad USB connection problem

I have been working on the bad USB connection, trying to debug the cause.
The issue is very strange, here are my findings:
- the following things happen with both my keyboard and my mouse in both USB 2.0 and 3.0, 
thus it is not to a device nor USB type
- when being in the login page, right after plugging the keyboard, 
I get the error -110 and the things I type are not registered in the terminal 
(which initially made me believe that there was a problem with the USB connections)
- if the keyboard is plugged in before boot, I see the error -110 in the log during boot, 
but then in the login page, the keyboard works and I can log in.
- when being in the login page, if I plug the keyboard and wait a little bit (~5-10 seconds), 
the PC tries to connect again and again to the keyboard until it succeeds 
(and correctly displays the name and brand of the keyboard in the logs).
- if I have the keyboard plugged in and correctly working, plugging in the mouse works almost immediately (same vice-versa).

Seeing this, I believe that the "problem" is not actually a problem and more like a "slow process" 
(in which the PC tries to connect to the USB devices).
Because I can always connect via SSH to my server and because I do not plan on connecting any storage via USB,
I will close the corresponding issue in GitHub about this problem.


# 2025/10/23 - Mitigating fan noise

Before doing anything about the fan noise, I measured how bad it is with the microphone of my smartphone 
(results may not be precise):
- background (server turned off): 40-42 dB
- server on and mic at 30cm from it: 45 dB
- server on and mic at 1cm from it: 50 dB

I disassembled the CD/DVD, SDD/HDD and both fans following [this video](https://www.youtube.com/watch?v=pP0L6xs-QMw).
For the rear fan (i.e. not the one for the CPU), I did not remove the motherboard, 
I just slightly bended one of the top aluminum pieces and was enough to remove the fan.
I have cleaned the fans (disassembled) and the CPU cooler (without disassembling it) using some toilet paper.
The cleaning did not reduce that much the noise from my server (which only comes from the fans).

The other thing I wanted to do is to adapt the fan curve so that the fans are not spinning 
if the CPU does not reach a certain temperature.
This (in theory) can be done both from the BIOS and the OS.
I did not have luck in the BIOS because the only setting I can change about the fans is their "idle mode", 
which was already set to the minimum (see `journal_media`).
In the OS, I did not have any luck either because I believe that the PWM of the fans is not exposed to the OS level.

As none of the two options worked, I searched more solutions. 
The reason I don't want to hear anything is because I can only have the server running in my room.
Other solutions that I found are:
- buying new good fans (e.g. some Noctua ones)
- try to do some noise isolation

The price of new fans is quite expensive compare to what the computer has cost me (15€*2 vs 50€).
I have access to cheap wood and tools, so I will most likely build an enclosure following [this video](https://www.youtube.com/watch?v=j8IYsQ6QVp8).
For the noise-dampening material, I have found pieces around 10-15€ in Praxis and Hornbach.
However, one needs to be careful with these materials because the foams are usually not "fire safe".
Based on this and the prices, I will first build an enclosure (without the noise-dampening material),
test the noise levels, and, if needed, I will add the noise-dampening material.


# 2025/10/25 - Enclousure for my server

I have bought the materials to build the enclosure, the main item is an MDF pane of 122x62 cm and 12mm of thickness (~8€).
I have attached a schematic and pictures in `journal_media`.
The design is very close to the one from [this video](https://www.youtube.com/watch?v=j8IYsQ6QVp8).

The server is now set up inside the enclosure and I cannot hear the fan noise.
In fact, I can hear more the fridge from my kitchen (one closed door away) than the server 
(although my fridge is kinda noisy for a fridge).
Therefore, I will not buy any acoustic foam to further dampen the noise from the fans.

I have been tracking the temperature of the CPU using this script:
```
#!/bin/bash

LOGFILE="/home/marc/tmp.txt"

for i in {1..1000}; do
    DATE=$(date '+%Y-%m-%d %H:%M:%S')
    TEMP_LINE=$(/usr/bin/landscape-sysinfo | grep "Temperature")
    echo "$DATE - $TEMP_LINE" >> "$LOGFILE"
    sleep 60
done
```
and the temperatures in the first couple of hours after turning on the server have all been between 34 and 38 degrees Celsius.
I am happy with these temperatures.


# 2025/10/26 - Monitor CPU temperature

I want to monitor the CPU temperature to know if the server is heating up.
Grafana allows one to visualize data from a CPU file in a local website and send email notifications.

First, I need to generate the CPU temperature data and store it in a CSV file.
This is done by the following script:
```
#!/bin/bash
LOGFILE="/home/marc/monitoring/data/cpu_temp.csv"

# Add header if file doesn't exist
if [ ! -f "$LOGFILE" ]; then
    echo "timestamp,temperature_cpu,temperature_zone0,temperature_zone1,temperature_zone2" > "$LOGFILE"
fi

DATE=$(date '+%Y-%m-%d %H:%M:%S')
TEMP_CPU=$(/usr/bin/landscape-sysinfo | grep -oP 'Temperature:\s*\K[0-9.]+')
TEMP_Z0=$(cat /sys/class/thermal/thermal_zone0/temp)
TEMP_Z0=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z0/1000}")
TEMP_Z1=$(cat /sys/class/thermal/thermal_zone1/temp)
TEMP_Z1=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z1/1000}")
TEMP_Z2=$(cat /sys/class/thermal/thermal_zone2/temp)
TEMP_Z2=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z2/1000}")

echo "$DATE,$TEMP_CPU,$TEMP_Z0,$TEMP_Z1,$TEMP_Z2" >> "$LOGFILE"
```
which is made executable and run every minute with `crontab`.

To install Grafana, I followed the instructions on [its documentation](https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/).
Then, I start it with:
```
sudo systemctl enable --now grafana-server
```
I can now check my grafana locally (in my laptop) in: http://myserver:3000 
(note that `myserver` is my server's name in the tailnet).

The initial credentials are `user: admin` and `password: admin`. 
Grafana tells you to update the password so I did.

Following the instructions on [the docs](https://grafana.com/blog/2025/02/05/how-to-visualize-csv-data-with-grafana/) 
on how to load CSV data on Grafana,
I have installed the `Infinity` data source with
```
grafana-cli plugins install yesoreyeram-infinity-datasource
```
and restarted Grafana
```
sudo systemctl restart grafana-server
```
Then, I went to `Connections > Data sources` inside Grafana's local website and clicked on `Infiinity`.
OK, so this data source is only able to load CSV files from HTTP requests.
I have added a small snipped that serves my recorded monitoring data for HTTP requests in 
`/etc/systemd/system/monitoring-data-http.service`.
```
[Unit]
Description=HTTP server for the monitoring data
After=network.target

[Service]
User=marc
WorkingDirectory=/home/marc/monitoring/data
ExecStart=/usr/bin/python3 -m http.server 8081
Restart=always

[Install]
WantedBy=multi-user.target
```
I activate this service with:
```
sudo systemctl daemon-reload
sudo systemctl enable monitoring-data-http.service
sudo systemctl start monitoring-data-http.service
```
and check that it works using:
```
sudo systemctl status monitoring-data-http.service
```
and that I can download the data from http://myserver:8081

Therefore, I will use http://myserver:8081/cpu_temp.csv to set up the `Infinity` HTTP request.
In the `Query > Parsing options & Result fields`, I specify the format of the columns (e.g. time, numeric...).
I am also setting up an alert so that I get an email if the temperature is above 55ºC.
To receive alerts via email, I need to set up SMTP by editing `/etc/grafana/grafana.ini`,
```
[smtp]
enabled = true
host = smtp.gmail.com:587
user = your-email@gmail.com
password = your-app-password
skip_verify = false
from_address = your-email@gmail.com
from_name = Grafana
```
and then restart Grafana using
```
sudo systemctl restart grafana-server
```
I have clicked on `Test` and I correctly receive a notification email.

I have changed the script so that the CPU temperatures get sampled every 10 seconds.
I have also disabled the data from temp_zone0 and temp_zone1 because they are static and do not change.
There is a "bug" in Grafana that it does not know that Europe is in "winter time" so that the time is shifted +1h.
I have tried connecting the dashboard to the Grafana app in my phone but I can only do the login via HTTP 
(not HTTPS as the app wants),
therefore I have just added a shortcut to the webpage in the home page of my phone.

To really test that everything works, I am going to stress the computer and rise its CPU temperature using:
```
sudo apt install stress
stress --cpu 4 --timeout 60
```
The mail works correctly.
One thing that I have realized is that Grafana assumes your timestamps to be in UTC time.
Mine are not in UTC and this gives this weird time conversion that Grafana does automatically.
I have changed it using `date -u '+%Y-%m-%d %H:%M:%S'`, where the `-u` flag is for UTC time.
I have also changed my contact point so that I do not receive emails when an alert is OK (after being triggered).


# 2025/10/28 - Bug in CPU-temperature monitoring script

I received an alert from Grafana saying that there was a data-source error for the CPU temperature.
There was a bug in the script to read the CPU temperature, in particular when making sure that the file has maximum 10000 lines.
Also, it was not logging the temperature for the time `HH:mm:50`. 

Here is the current version, which solves both issues:
```
#!/bin/bash
LOGFILE="/home/marc/monitoring/data/cpu_temp.csv"
MAX_LINES=10000

# Add header if file doesn't exist
if [ ! -f "$LOGFILE" ]; then
  echo "timestamp,temperature_cpu,temperature_zone0,temperature_zone1,temperature_zone2" > "$LOGFILE"
fi

for i in {1..6}; do
  DATE=$(date -u '+%Y-%m-%d %H:%M:%S') # UTC format for Grafana
  TEMP_CPU=$(/usr/bin/landscape-sysinfo | grep -oP 'Temperature:\s*\K[0-9.]+')
  TEMP_Z0=$(cat /sys/class/thermal/thermal_zone0/temp)
  TEMP_Z0=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z0/1000}")
  TEMP_Z1=$(cat /sys/class/thermal/thermal_zone1/temp)
  TEMP_Z1=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z1/1000}")
  TEMP_Z2=$(cat /sys/class/thermal/thermal_zone2/temp)
  TEMP_Z2=$(awk "BEGIN {printf \"%.1f\", $TEMP_Z2/1000}")

  echo "$DATE,$TEMP_CPU,$TEMP_Z0,$TEMP_Z1,$TEMP_Z2" >> "$LOGFILE"

  # store only the last lines
  LINE_COUNT=$(wc -l < "$LOGFILE")
  if (( LINE_COUNT > MAX_LINES + 1 )); then
    DATA=$(tail -n "$MAX_LINES" "$LOGFILE")
    printf "timestamp,temperature_cpu,temperature_zone0,temperature_zone1,temperature_zone2\n${DATA}\n" > "${LOGFILE}"
  fi

  sleep 10
done
```


# 2025/10/30 - Installing Immich and phone backup

From the [Immich docs](https://docs.immich.app/install/docker-compose/), it is recommended to install Immich via Docker compose.
Therefore first I need to install Docker. 
Following the [Docker installation guide](https://docs.docker.com/engine/install/ubuntu/), 
I first check that I don't have any docker package installed:
```
apt list --installed | grep docker
```
Regarding the firewall precautions, I will build the Docker container such that it can only talk to devices in my tailnet
(which I trust), see [issue #17](https://github.com/MarcSerraPeralta/homelab/issues/17).
Immich recommends installing Docker using `apt`, so I will do that following the Docker guide.
After the installation, I have checked that Docker is running using:
```
sudo systemctl status docker
```
and 
```
sudo docker run hello-world
```
which showed that Docker is active and that it works correctly.

I continue following the installation guide for Immich and download the docker configuration files.
I have changed the following lines from `docker-compose.yml`:
```
ports:
  - "100.104.237.106:2283:2283"
```
and from `.env`:
```
# The location where your uploaded files are stored
UPLOAD_LOCATION=/srv/immich/library

# The location where your database files are stored. Network shares are not supported for the database
DB_DATA_LOCATION=/srv/immich/postgres

# To set a timezone, uncomment the next line and change Etc/UTC to a TZ identifier from this list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
TZ=Europe/Amsterdam

# Connection secret for postgres. You should change it to a random password
# Please use only the characters `A-Za-z0-9`, without special characters or spaces
DB_PASSWORD=postgres # I have changed it but I won't put it here
```
I have run the following commands to create the Immich directory:
```
sudo mkdir -p /srv/immich
sudo chown -R $USER:$USER /srv/immich
```
One also needs to add himself to the docker group so that `docker compose up -d` runs correctly:
```
sudo usermod -aG docker $USER
newgrp docker
```
Now, I can (for example) run `docker ps`, which works (as I have correct permisions).
After running the Immich docker, I test that it is working correctly using:
```
docker ps
```
_Note: server temperature hit 50ºC during `docker compose up -d` but then went back to 40ºC._

I have also run:
```
sudo ss -tulpen | grep 2283
```
to check that the IP port is only comming from the tailnet IP, not the LAN IP.

After installing Immich, I follow the postinstallation steps from the [Immich docs](https://docs.immich.app/install/post-install):
- I have enabled to use "Chrome cast". 
- I have enabled "Storage Template" so that the pictures are auto-organized inside the provided template name.
- I have created a quota for my user of 10GB.

I have installed the Immich app on my phone and then logged in.
I have selected to backup the "Camera", "WhatsApp Images", and "WhatsApp Video" albums.
Then I have enabled backup.

During the upload of the pictures + face recognition, the CPU temperature spiked to 60ºC.
I should disable face recognition for this backup because the picutres are going to get moved to the external one.
This way I don't waste CPU resources identifying the faces.


# 2025/10/31 - Grafana dashboard for Immich and choice of hardware storage

I have added a dashboard in Grafana for Immich, which reports the storage usage and the number of photos and videos.
This can be done using the Immich API (+ API key) through URL requests, which returns JSON data.
For more information, see [issue #21](https://github.com/MarcSerraPeralta/homelab/issues/21).

I have also solved a problem with the automatic background backup in my Xiaomi phone, see [issue #24](https://github.com/MarcSerraPeralta/homelab/issues/24).

I have been researching about the SATA connectors in the motherboard to know which hardware I should use for storage.
In `hp_elitedesk_g1_800_usdt`, there is an explanation of the SATA connectors.
To know the storage I need, I have also checked how much storage I currently require:
- 165GB of media and documents
- 115GB of backup for my ThinkPad

The server OS is currently installed in a SATA SSD of 256GB in the standard SATA port of the motherboard.
I will buy the following:
- mSATA SSD of 256GB for the OS + Immich phone backup + maybe some documents [~30€]
- SATA 2.5inch SSD of 1TB for the media, documents, backup of ThinkPad, archive of emails, media center... [~60€]

In case I need more storage, I can always buy the slimline SATA adapter to SATA 
(in the shape of an optical bay) and another 1TB of 2.5inch SSD storage.
I can also buy an SSD of 2TB, although they start to be more pricey (60€ vs 120€).

The reason for using SSDs instead of HDDs is that the "NAS" HDDs are 3.5inch and cannot be mounted in my server. 
Also, my father has been running the same 1TB SSDs in the family NAS for several years now and we haven't had any problem.

For the backup of the cluster, I will use the 512GB and 1TB HDDs that I already have for media and backups.

Regarding the storage for the media center, I plan on only storing the current series 
that I am watching or movies that I want to watch.
I don't plan on having a huge library nor movies or series at 4K resolution.
I will probably have 400GB of storage for the media center. 
One hour of 1080p or 1440p video takes 2GB-5GB of space, therefore I will be able to store ~100 hours of playtime.
This is plenty enough to store a couple of seasons of the TV shows that I am watching, which is perfect for me.


# 2025/11/01 - Security webcam installation and storage structure description

I have been thinking on how I am going to categorize everything inside my server.
Here is what I plan on doing:

mSATA SSD 256GB (with Ubuntu Server)
```
/home/marc/
        |- monitoring/
           |- log_cpu_temperature.sh
           |- log_disk_usage.sh
           |- log_ram_usage.sh
           |- log_network_usage.sh
        |- config_files/
           |- immich/ ...
/srv/
 |- monitoring/
     |- cpu_temperature.csv
     |- disk_usage.csv
     |- ram_usage.csv
     |- network_usage.csv
 |- immich/ ... (for phone backup)
```
SATA SSD 1TB
```
/
|- immich/ ... (for external library)
|- email_archive/ ...
|- jellyfin/ ... 
|- backups/
    |- thinkpad/ ...
|- music/
|- books/
|- education/ ... (uab, tu delft, bojos, joves, praeludium, nostra llar, industrial, teyca, uoc, crm, ...)
|- arts_and_crafts/ ... (doodle, recipes, origami, dancing_lessions, presents, ...)
|- documents/
    |- token_keys/ 
    |- visa_countries/
    |- monthly_expenses/
    |- certificates/
    |- administration/
    |- cards/
    |- health/
    |- banks/
```

As a side note, I will use `df` to monitor disk usage every 1h,
`free` to monitor ram usage every 10s, 
and `/sys/class/net/eno1/statistics` to monitor network usage very 1s.
This will be displayed in a Grafana dashboard.

Today I have recieved the TP-Link Tapo C200.
I have followed the instructions in the included guide and I have set up the camera with the phone app.
I have also assigned the camera a static IP address so that I could access it through the tailnet.
However, apparently, the camera also works when I am not connected to the local wifi and I have tailscale disabled.
I will keep the static IP, but it is not necessary.

I have disabled IR vision in the camera because it reflects on my windows and I cannot see the street. 
The normal camera works fine because I have a street lamp 15-20 meters away from my window.

Regarding the storage, as I will (most likely) have install again Ubuntu Server in the mSATA drive,
I will try to play with the home server and install as many things as I can so that I know how they behave.

First I will start with Jellyfin (for media center).
I am following the installation guide for bare metal from [its documentation](https://jellyfin.org/docs/general/installation/linux/).
During the setup, I have disabled "Allow remote connections to this server" because I already have Tailscale.
Because I have disabled the remove access, 
then I need to access jellyfin on my browser using the tailnet IP (jellyfin uses port 8096).
This is a little bit described in the [Jellyfin docs](https://jellyfin.org/docs/general/post-install/networking/tailscale).
I am having problems with accessing the Jellyfin server.
I will continue debugging another day.


# 2025/11/06 - Running Jellyfin

I have checked that the Jellyfin service is active using `systemd` 
and that Jellyfin is listening to anything in port 8096:
```
sudo ss -tulpen | grep 8096
```
I can load `http://100.104.237.106:8096`, but Jellyfin tells me to add a server.
Trying `100.104.237.106:8096` or `192.168.0.50` results in the following message:
```
Connection Failure
We're unable to connect to the selected server right now. 
Please ensure it is running and try again.
```
The first thing I tried is uninstalling jellyfin (`sudo apt remove jellyfin`) and
running the installation script again. 
However, the problem persisted.

Looking at the logs from Jellyfin (in `/var/log/jellyfin`), I see the following lines:
```
[2025-11-06 19:25:52.562 +01:00] [WRN] Blocking request to "%2fSystem%2fInfo%2fPublic" by "100.90.224.7" due to IP filtering rule, reason: RejectDueToRemoteAccessDisabled
```
and 
```
[2025-11-06 19:29:04.158 +01:00] [INF] Defined LAN subnets: ["127.0.0.1/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
[2025-11-06 19:29:04.158 +01:00] [INF] Defined LAN exclusions: []
[2025-11-06 19:29:04.159 +01:00] [INF] Used LAN subnets: ["127.0.0.1/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
[2025-11-06 19:29:04.160 +01:00] [INF] Filtered interface addresses: ["127.0.0.1", "192.168.0.50", "172.18.0.1", "100.104.237.106"]
[2025-11-06 19:29:04.160 +01:00] [INF] Bind Addresses ["0.0.0.0"]
[2025-11-06 19:29:04.160 +01:00] [INF] Remote IP filter is "Allowlist"
[2025-11-06 19:29:04.160 +01:00] [INF] Filtered subnets: []
```

The problem is with the IP filtering rule, which is set as `"Allowlist"`.

I have tried editing the config files in `/var/lib/jellyfin/config/`, but the directory is empty. 
Searching on the web, I have seen that if the Jellyfin installation is done bare metal, 
then the config files are inside `/etc/jellyfin/`.

I have edited the file `/etc/jellyfin/network.xml`, in particular, I have changed the line `<LocalNetworkSubnets />` to:
```
  <LocalNetworkSubnets>
    <string>127.0.0.1/8</string>
    <string>10.0.0.0/8</string>
    <string>172.16.0.0/12</string>
    <string>192.168.0.0/16</string>
    <string>100.64.0.0/10</string>
  </LocalNetworkSubnets>
```
To apply the changes, I restard Jellyfin:
```
sudo systemctl restart jellyfin
```

Then, when opening `http://100.104.237.106:8096`, I get the "Welcome to Jellyfin!" screen 
and the setup guide for my server.
Again, during the setup, I have left the "Allow remove access" option unchecked (so not allowed).
Now, after clicking "Finish", I get a "Please sign in" screen and I can log in.
I can also log in using the Jellyfin app on my phone.


# 2025/11/07 - Adding media to Jellyfin

From the [Jellyfin documentation](https://jellyfin.org/docs/general/clients/codec-support/), 
the best native supported codec is H.264 8Bit, 
which does not require the server to transcode the media format on the fly when media gets played.
This is good to reduce the stress and power consumption in the server.
A command to convert any video format to H.264 8Bit is:
```
ffmpeg -i input_video.ext -c:v libx264 -pix_fmt yuv420p -preset slow -crf 23 -c:a copy output_video.mp4
```
To check if a video is in H.264 8Bit format, run:
```
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,pix_fmt -of default=nw=1 movie_h264.mp4
```
and should see the following output:
```
codec_name=h264
pix_fmt=yuv420p
```

I can do the transcoding in my laptop, which has better hardware and then copy the files to the server with:
```
rsync -avhP --progress /path/to/converted/videos/ marc@100.104.237.106:/srv/jellyfin
```
I hav added my user as owner of the jellyfin directory:
```
sudo chown -R marc:marc /srv/jellyfin/
```
because, if not, one requires `sudo` priviledges to copy the files.
I can do this because this is a home server and I am only giving my user access to the jellyfin directory,
which only stores movies and shows that I want to watch.

To check that everything works correctly, 
- I have donwloaded some Public Domain media from `archive.org`
(which I have checked that have a correct entry in `imdb.com`).
- I have converted the files to H.264 8Bit using the previous command 
and checked that they have the correct encoding.
- Because I have downloaded some shows, I will copy them to `/srv/jellyfin/Shows/"{Series Name} ({year})"/"Season {n}"/`
as described in the [Jellyfin docs](https://jellyfin.org/docs/general/server/media/shows/).
- I have added the Library to my Jellyfin server

The CPU temperature of my server does not increase when playing the videos.

I have installed the following plugins for Jellyfin:
- AniDB
- AudioDB
- Fanart
- MusicBrainz
- OMDb
- Playback Reporting
- Studio Images
- TheTVDB
- TMDb

I have added a new TV show and the cover image was shown without any configuration.
I have used the `imdbid-...` tag in the name of the TV show.


# 2025/11/09 - Setting up Caddy (reverse proxy) (part 1)

I have installed Caddy to use as a reverse proxy:
```
sudo apt install caddy
```
Then I have added to the Caddyfile in `/etc/caddy/Caddyfile` the following:
```
:8080 {
        # Set this path to your site's directory.
        root * /usr/share/caddy

        # Enable the static file server.
        file_server

        # Another common task is to set up a reverse proxy:
        #reverse_proxy localhost:2283

        # Or serve a PHP site through php-fpm:
        # php_fastcgi localhost:9000
}

# Refer to the Caddy docs for more information:
# https://caddyserver.com/docs/caddyfile

http://pihole.local:8080 {
        reverse_proxy 100.104.237.106:80
}

http://immich.local:8080 {
        reverse_proxy 100.104.237.106:2283
}

http://jellyfin.local:8080 {
        reverse_proxy 100.104.237.106:8096
}
```
where I have changed the default Caddy port from `80` to `8080` because it was overlapping with pi-hole's port.

I have added the `X.local` websites in the local DNS table of the pi-hole using the WebUI.
I have also allowed port 8080 in the firewall:
```
sudo ufw allow 8080/tcp
sudo ufw reload
```

There is a problem when reaching the `X.local` websites, 
but I will continue debugging later.


# 2025/11/11 - Setting up Caddy (reverse proxy) (part 2)

I have run test to check what is going wrong:

1. Running `curl -v http://192.168.0.50:8080` from a different LAN device returns an HTTP response
1. Running `curl -v http://localhost:8080` inside the server returns:
```
HTTP 502 Bad Gateway
```

After some debugging, I have realized that `.local` is used for something called `mDNS`.
If I just change all the names to `X.home`, then everything works correctly.
Note that for pi-hole, one needs to use `http://pihole.immich:8080/admin`.

Currently everything works if I use `:8080` port for caddy (because pi-hole uses port 80).
I do not want to type 8080 in the website name to access the websites.
One solution would be to edit pi-hole's config and forward hostnames `X.home` to Caddy (in port 8080).


# 2025/11/12 - Setting up Caddy (reverse proxy) (part 3)

I have done some research and now I understand the problem with Caddy and Pi-hole for port 80.

Pi-hole actually implements two things:
- DNS server for the ad blocking (`pihole-FTL`)
- web server (using port 80 HTTP/S) so that the admin panel can be "served" in the browser 
(i.e. one does not have to use the terminal to check the status of the pi-hole DNS server)

Pi-hole's web server uses lighttpd, which is capable of reverse proxying.
However, I want to use Caddy, because it is much easier to configure and it has HTTPS by default.

The problem is that I am trying to install Caddy when lighttpd is already installed and running.
They are both web servers and ideally should listen to port 80, but they cannot do it at the same time.
I have this problem because I am running both pi-hole and Caddy on the same PC.

The solution is to remove lighttpd and configure Caddy to serve the admin panel for the pi-hole.
Thus I will only have Caddy installed and it will be able to listen to port 80 without any conflict.
I can then use Caddy as my reverse proxy for all my other applications (e.g. jellyfin, immich...).
The only thing I need to ensure is that Caddy has the dependencies to run the PHP website of pi-hole 
(check this [forum post](https://caddy.community/t/using-caddy-instead-of-lighttpd-with-pi-hole/8087)).

Now, I am going to implement the solution from the forum post:
```
service lighttpd stop
sudo apt install php8.3-fpm   
sudo systemctl enable php8.3-fpm
sudo systemctl start php8.3-fpm
```
Then I edit the contents of the Caddyfile with `sudo vim /etc/caddy/Caddyfile` and change them to:
```
http://pihole.home {                                                                                                             
    root * /var/www/html
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```
Finally, 
```
sudo systemctl stop caddy
sudo systemctl start caddy
```
So this was not all of it, because `pihole-FTL` is also using port 80.
However, this can be easily solved because `pihole-FTL` is only using this port to show a
blocking page message, but it can be disabled.
I will change it by switching the blocking mode to `NULL`, 
so that it returns a NULL result instead of a page when blocking.
```
sudo pihole-FTL --config dns.blocking.mode NULL
sudo systemctl stop pihole-FTL # frees port 80
sudo systemctl start caddy # takes port 80
sudo systemctl start pihole-FTL # does not throw an error if it cannot access port 80
```
Pi-hole uses port 53 for the DNS server.
In its config file, it says `80o` which means that port 80 is optional (for the web server).

I seems that now there is no problem with the ports, 
but now the pihole admin page is empty (`http://pihole.home/admin` nor `http://100.104.237.106/admin`).

The problem is that pihole verion 6 uses `.lp` files (which are lighttpd script files)
and not `.php` files. Therefore, it is not possible to use Caddy+php to render the website.

This is the solution that I now have in mind:
- Caddy to handle all normal sites (like immich.home, jellyfin.home, etc.) on port 80/443
- Lighttpd to stay installed only for Pi-hole’s admin panel, but listening on port 8001 

This way there's no port conflict, and I can make Caddy reverse-proxy to lighttpd so that 
I can just visit `http://pihole.home` (without the :8001).

I will continue configuring Caddy+pihole another day.


# 2025/11/13 - Setting up Caddy (reverse proxy) (part 4)

I just realized that now pihole is not working correctly: it is not blocking the ads.
Even after stoping caddy and restarting pihole (so that it can use port 80),
the ad-blocking capabilities do not work. 
Even if I start lighttpd it does not work.

I have been reading my journal about my installation of pihole (2025/10/09).
It is weird because I disabled lighttpd (although I believed that it is needed to render the WebUI).
I have to research a little bit more about this, but I will probably do the following:
- uninstall pihole and lighttpd (keep caddy installed)
- make caddy listen to port 80 (for HTTP(S) handling)
- install pihole
- set the pihole's websever to use to something that is not port 80 (used by caddy)
- if needed, I will install lighttpd (although actually I believe it is not needed)

First,
```
sudo apt remove lighttpd
sudo pihole uninstall
```
Afterwards, I had to change back the DNS settings for the LAN (in the router) and the tailnet.
I have also reinstalled caddy:
```
sudo apt remove caddy
sudo apt install caddy
```
So, I made a mistake because the change in the router's DNS only gets applied after rebooting the router.
Currently, I am not at home so I cannot reboot it.
Because of that, I cannot run `sudo apt install caddy` because `apt` cannot correctly resolve the hostnames.


# 2025/11/16 - Reinstalling pihole and caddy

I have removed my home server as DNS in my router and I have reset the router to apply the changes.
The server still cannot resolve the domain names (e.g. `ping google.com` does not work).
I don't know what I have done because I turned tailscale down and I had some problems sshing to the server.
I believe the problem was the flag `--accept-dns=false` in tailscale.
Now I can do `ping google.com`.

I want to do a fresh install of everything related to caddy and pihole, so I have uninstalled caddy, pihole, lighttpd...

First, I have installed Caddy and checked that it is using port 80 and 443:
```
sudo apt install caddy
sudo ss -tulpen | grep "caddy"
```
it is not, because the Caddyfile does not specify that I want caddy to listen to ports 80 and 443.
I changed it (`sudo vim /etc/caddy/Caddyfile`) to:
```
:80 {
        # Set this path to your site's directory.
        root * /usr/share/caddy

        # Enable the static file server.
        file_server

        # Or serve a PHP site through php-fpm:
        #php_fastcgi unix//run/php/php8.3-fpm.sock
}

:443 {
        # Set this path to your site's directory.
        root * /usr/share/caddy

        # Enable the static file server.
        file_server

        # Or serve a PHP site through php-fpm:
        #php_fastcgi unix//run/php/php8.3-fpm.sock
}
```
and then restarted caddy:
```
sudo systemctl restart caddy
sudo ss -tulpen | grep "caddy"
```
Now it uses ports 80 and 443.

Secondly, I reinstall pihole:
```
curl -sSL https://install.pi-hole.net | sudo bash
```
I have set it up using the same options as I had before.
I cannot access `192.168.0.50:80/admin` because I have Caddy running in port 80.
I have checked (`sudo ss -tulpen`) and `pihole-FTL` is only using port 53 (for DNS requests).
To access pihole's web UI, I edit its configuration file (`sudo vim /etc/pihole/pihole.toml`):
```
port = "8080o,80o,443os,[::]:80o,[::]:443os"
```
and then I restart `pihole-FTL` (I don't know if this is necessary):
```
sudo systemctl restart pihole-FTL
sudo systemctl status pihole-FTL
sudo ss -tulpen | grep "pihole"
```
Now I can see that `pihole-FTL` is using ports 53 and 8080.
I can access pihole's web UI in `192.168.0.50:8080/admin`.
It is also useful to change the pihole password using:
```
sudo pihole setpassword
```

Thirdly, let's check that I can use a custom domain name for pihole.
1. make sure to add back again the home server as DNS server in the router.
1. add `pihole.home` <-> `192.168.0.50` as record in the Local DNS section of pihole's Web UI.
1. add the following to `/etc/caddy/Caddyfile`:
```
http://pihole.home {
        @root path /
        rewrite @root /admin

        reverse_proxy 192.168.0.50:8080
}
```
Now, I can access pihole's web UI using `http://pihole.home`.

Finally, let's add my server back to my tailnet:
```
sudo tailscale up --accept-dns=false --advertise-exit-node --advertise-routes=192.168.0.0/24
```

Because I turned off tailscale in the server, I got an error from immich.
I could solve it by just running:
```
cd /path/to/docker-compose/file
docker compose down
docker compose up -d
```

I have also added immich and jellyfin domain names in the local DNS of pihole,
and also in `/etc/caddy/Caddyfile`:
```
http://jellyfin.home {
        reverse_proxy 192.168.0.50:8096
}

http://immich.home {
        reverse_proxy 100.104.237.106:2283
}
```


# 2025/11/17 - Caddy certificates for HTTPS

I have changed the Caddyfile to create its own CA certificates:
```
http://pihole.home {
        tls internal
        @root path /
        rewrite @root /admin

        reverse_proxy 192.168.0.50:8080
}

http://jellyfin.home {
        tls internal
        reverse_proxy 192.168.0.50:8096
}

http://immich.home {
        tls internal
        reverse_proxy 100.104.237.106:2283
}
```
The root certificate is in `/var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt`.
I have downloaded the certificate to my local laptop using:
```
ssh -t marc@myserver "sudo cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt" > root.crt
``` 
To install the certificate in my Linux Mint, I run the following commands:
```
sudo mkdir /usr/local/share/ca-certificates/extra
sudo cp root.crt /usr/local/share/ca-certificates/extra/root.crt
sudo update-ca-certificates
trust list # prints the installed certificates
```
Then, I have to load the certificate in Mozilla Firefox.
Following the instructions in [issue #29](https://github.com/MarcSerraPeralta/homelab/issues/29),
I have installed the certificate in Mozilla Firefox.
However, when I type `https://pihole.home` I get a `Secure Connection Failed` error.
Restarting Firefox does not seem to solve the problem.
I have also installed the certificate in my phone, where I can use Google Chrome.
I can't open the HTTPS version of the website.
I was stupid because the Caddyfile only has the HTTP version of the websites.
```
pihole.home {
        tls internal
        @root path /
        rewrite @root /admin

        reverse_proxy 192.168.0.50:8080
}


jellyfin.home {
        tls internal
        reverse_proxy 192.168.0.50:8096
}

immich.home {
        tls internal
        reverse_proxy 100.104.237.106:2283
}
```
For Firefox in Android, I had to follow the following steps:
1. Install CA certificate (this is done in the phone "Configuration" app, so it varies depending in OS)
1. Open Firefox
1. Go to Settings → About Firefox.
1. Tap the Firefox logo five times.
1. Navigate to Settings → Secret Settings.
1. Toggle Use third party CA certificates.

Now all the HTTPS work (both in my laptop and phone, which both use Firefox).

I have also added the grafana website link:
1. Add `grafana.home` in the local DNS table
1. Update the Caddyfile to do a reverse proxy to the correct port (port 3000)


# 2025/11/18 - Setting up qBitTorrent and ProtonVPN in my laptop

I want to set up my laptop to download torrents using qBitTorrent and ProtonVPN (to not expose my IP when torrenting).
First, I install the ProtonVPN GUI for Ubuntu (because I am using Linux Mint) following the [ProtonVPN guide](https://protonvpn.com/support/official-linux-vpn-ubuntu/):
```
wget https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.8_all.deb
sudo dpkg -i ./protonvpn-stable-release_1.0.8_all.deb && sudo apt update
sudo apt install proton-vpn-gnome-desktop
```
This commands didn't work. I get a `unable to locate package proton-vpn-gnome-desktop` error.
I have found the following commands that actually work:
```
sudo apt purge ~nprotonvpn
sudo apt autoremove
sudo apt update
sudo apt install gdebi
sudo gdebi protonvpn-stable-release_1.0.8_all.deb
sudo apt install proton-vpn-gnome-desktop
```
I have also installed the CLI version:
```
sudo apt install proton-vpn-cli
```

I have purchased Proton VPN Plus during black friday and I am sharing it with some friends,
so it only costs me 1€/month. I have chosen Proton VPN because it has no logs policy (which has been verified)
and because it is well reputated.

I have installed qbittorrent following [its documentation](https://launchpad.net/~qbittorrent-team/+archive/ubuntu/qbittorrent-stable):
```
sudo add-apt-repository ppa:qbittorrent-team/qbittorrent-stable
sudo apt update
sudo apt install qbittorrent
```
Before activating ProtonVPN, I have run the check with `ipleak.net` described in [issue #31](https://github.com/MarcSerraPeralta/homelab/issues/31).
If I do not have ProtonVPN activated, I get my IP address.
If I activate ProtonVPN, I get three IP addresses, one of which is my IP address.
If I bind qbittorrent to only use the VPN ([described here](https://protonvpn.com/support/bittorrent-vpn)), 
then I do not see my IP address.
If I do not have the VPN activated, then the download does not start because it does not have internet,
which I can also see in `ipleak.net`.

Looking through the settings in ProtonVPN GUI, I can see the following ones which I should investigate further:
- Kill switch
- Port forwarding

Regarding the kill switch in the ProtonVPN GUI, I actually do not need to set it up globally
because I already set up a kill switch in qbittorrent (when binding it to only use the VPN) [also see this post](https://www.ghacks.net/2016/03/23/qbittorrent-block-transfers-vpn-disconnect/).

In the meantime, I have also enabled annonymous mode in qbittorrent (Tools > Settings > Bittorrent).
I wanted qbittorrent to print my external IP address, but then I realized that I do not have the latest version 
because I do not have the latest Linux Mint version.
I need then to use flatpak:
```
sudo apt remove qubittorrent
sudo apt autoremove
flatpak install flathub org.qbittorrent.qBittorrent
```
Now I am running the newest version. I have run the same setup and checks as before.
I have also added some dark theme (see `qbittorrent/`).
The external IP shows the correct IP (i.e. the one from my VPN).
When I am not connected via VPN, it shows `N/A`.
I have also set up the configuration in qbittorrent such that when I close it, it actually gets closed (not minimized).

Regarding `ipleak.net`, I can still see some entries in the DNS section comming from the Netherlands,
although they come from North Holland and I am in South Holland. 
First, I have disabled Firefox own DoH: `Settings > Privacy > DNS over HTTPS`.
This didn't work.
I have checked the output of 
```
resolvectl status
```
and I see that there is a link usng tailscale.
When I turn off tailscale, then I cannot see any ducth DNS ISP in `ipleak.net`.
Having checked some things with ChatGPT (so I am not 100% sure), 
looks like my pihole may be giving the real country but there is no DNS leak.
Nevertheless, I will turn off tailscale whenever I run qbittorrent, just in case.


# 2025/11/19 - Useful scripts for Jellyfin

I have some media collection that I want to process for Jellyfin, this involves:
- Transcoding all the files
- Setting up the file structure and naming convention that Jellyfin wants

I have checked that I have an Intel iGPU in my laptop that supports H264 transcoding.
So I am using that when converting the files with ffmpeg (the script can be found in `jellyfin`).
For that, I had to install vainfo:
```
sudo apt install vainfo
```

To host all these media in my server, I have also expanded its logical volume to maximum:
```
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
```
When I reinstall the server in the mSATA drive, 
I am not going to do this logical volume and just have all the disk available.

Checking the codec formats supported by Jellyfin, I see that `H.265 8Bit` (or `HEVC`)
is also supported in most cases (except with some warnings about old versions of browsers).
Because HEVC is much better at compression, I will use it across all media.

I still need to think what is the best way of manipulating the media files.


# 2025/11/20 - Grafana dashboard for Jellyfin

In the [Jellyfin docs](https://jellyfin.org/docs/general/post-install/networking/advanced/monitoring/), 
it shows how to enable Prometheus metrics in Jellyfin (which can be added to Grafana).
To enable it, edit `/etc/jellyfin/system.xml` and change this line from `false` to `true`:
```
<EnableMetrics>false</EnableMetrics>
```
Now I need to install prometheus in my server, but I will do later.


# 2025/11/21 - Notifications from new seasons and episodes

I want to have a tool that notifies me of new seasons and new episodes.
Currently I have a list of TV shows that I am following but I always forget to check for new episodes.
I have found `seasonwatch` which is a light Python tool that uses "The Movie DataBase" (TMDB)
to get the releases of new seasons and episodes.
To install it, I had to run
```
pip install PyGObject==3.50.0
pip install seasonwatch --no-build-isolation
```
The documentation on how to update the list of watched shows can be found in [its GitHub](https://github.com/gevhaz/seasonwatch).
My current list is the following (`seasonwatch tv -l`):
```
┌────────────────────────┬─────────────────────┬─────────────────────────────────────┐
│ Title                  │ Last watched season │ Hyperlink                           │
├────────────────────────┼─────────────────────┼─────────────────────────────────────┤
│ Final Space            │ 3                   │ https://www.themoviedb.org/tv/74387 │
│ Scissor Seven          │ 4                   │ https://www.themoviedb.org/tv/79141 │
│ Big Mouth              │ 7                   │ https://www.themoviedb.org/tv/74204 │
│ Rick and Morty         │ 7                   │ https://www.themoviedb.org/tv/60625 │
│ Sex Education          │ 3                   │ https://www.themoviedb.org/tv/81356 │
│ Love, Death and Robots │ 3                   │ https://www.themoviedb.org/tv/86831 │
└────────────────────────┴─────────────────────┴─────────────────────────────────────┘
```
and it returns the releases of new seasons when executing `seasonwatch`:
```
Season 5 of Scissor Seven is out already!
Season 8 of Big Mouth is out already!
Season 8 of Rick and Morty is out already!
Season 4 of Sex Education is out already!
Season 4 of Love, Death and Robots is out already!
No season 4 found for Final Space
```
I need to pipe this into a cron job and send me some kind of notification when a new season is out.


# 2025/11/24 - Installing `seasontracker`

The current python in the server does not have pip install nor venv.
When trying to run `python3 -m venv` I got told to install the following, which I do
```
sudo apt install python3.12-venv
```
Then I run the following commands:
```
cd ~/config_files/seasontracker
git clone https://github.com/MarcSerraPeralta/seasontracker.git
cd seasontracker/
python3 -m venv venv
source venv/bin/activate
pip install .
```
Then I configure the `seasontracker` and set up a cron job for `run_seasontracker.sh`:
```
source /home/marc/config_files/seasontracker/venv/bin/activate
seasontracker notify /home/marc/config_files/seasontracker/my_tracked_seasons.yaml
deactivate
```
with 
```
crontab -e
```
every first day of the month at 8am using `0 08 1 * *`.


# 2025/11/26 - Installing Intro skipper for Jellyfin

I want an intro skipper for jellyfin.
The most popular option seems to be [this one](https://github.com/intro-skipper/intro-skipper/).
I have followed the installation guide from [its wiki](https://github.com/intro-skipper/intro-skipper/wiki/Installation#step-1-install-the-plugin).
However, after adding the repository to Jellyfin, I could not see the plugin in the "Available list of plugins".
The reason was that my Jellyfin version was 10.11.2, while this plugin requires >=10.11.3.
I just upgraded my jellyfin version with
```
sudo apt update
sudo apt upgrade
```
Then, I could see the plugin. 
I have installed it, restarted jellyfin, and run detection software for intro scenes.
I have tried it with an episode of One piece (which has a recap followed by the intro),
and it manages to detect the intro section and create a "Skip intro" button.


# 2025/11/30 - Using Jellyfin for music

I have been aware that Jellyfin can also be used like a self-hosted Spotify.
It only requires installing an app that "mimics Spotify" like `Fineamp`, which is available in Google Play and iOS.
Then I just need to add a library to Jellyfin that contains the music media.
The app works well. 
I have switched to the beta release because it has better UI (they have redesign it).
The music library works quite well, but the files I have are not properly labelled so I have some incorrect categorization of songs.
I will dig into that because the [Jellyfin documentation](https://jellyfin.org/docs/general/server/media/music/) is not very extensive.

I have also made Jellyfin report the metrics, so that they can be used by Prometheus and Grafana.
This was done by repeating the steps from 2025/11/20. 
I believe this configuration was reseted when updating Jellyfin, but I am not sure.
Now, when I do:
```
curl http://myserver:8096/metrics
```
I get information about Jellyfin.
Now this needs to be pipelined to Prometheus, and then from Prometheus to Grafana.


# 2025/12/03 - Metadata for Jellyfin music and installing prometheus

The music metadata in Jellyfin gets taken from the `.mp3` file's metadata.
It is still important to structure correctly the files in directories because
the images for each artist and disc are stored there.
I have set up my music metadata provider for Jellyfin to be MusicBrainz because 
it has a useful program that can be used to replace the metadata of the `.mp3` for the correct one.
I have also manually added the images for the discs and the artists 
(they are all called `folder.jpg` and are located in each of the directories)
because Catalan music bands do not have images in the FanArt database.

I am installing prometheus following [this guide](https://www.cherryservers.com/blog/install-prometheus-ubuntu).
First, create the prometheus directories for storing the config files and the data (resp.):
```
sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus
```
Then download prometheus from the official repo:
```
wget https://github.com/prometheus/prometheus/releases/download/v3.5.0/prometheus-3.5.0.linux-amd64.tar.gz
tar vxf prometheus*.tar.gz
cd prometheus*/
```
Then install prometheus:
```
sudo mv prometheus /usr/local/bin/
sudo mv promtool /usr/local/bin/
```
Move the configuration file:
```
sudo mv prometheus.yml /etc/prometheus/
```
Create a system service for prometheus:
```
sudo vim /etc/systemd/system/prometheus.service
```
with the following content:
```
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=marc
Group=marc
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \

[Install]
WantedBy=multi-user.target
```
and then start the service:
```
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl status prometheus
```
so there is an error with prometheus because the service failed to start.
The reason is that it does not have the correct permisions to edit files in `/var/lib/prometheus/`.
This can be solved by:
```
sudo chown -R marc:marc /var/lib/prometheus
```
Then, prometheus is active and running with:
```
sudo systemctl start prometheus
sudo systemctl status prometheus
```
Finally, allow to use the port for prometheus Web interface:
```
sudo ufw allow 9090/tcp
```
which I can access in my laptop using:
```
http://100.104.237.106:9090/
```
For convenience, I have also added prometheus website to Caddy and to pihole (`prometheus.home/`).

To add the jellyfin metrics to prometheus, I have edited the prometheus config (`/etc/prometheus/prometheus.yml`)
by adding the following lines under `scrape_configs:`:
```
  - job_name: "jellyfin"
    metrics_path: /metrics
    static_configs:
      - targets: ["localhost:8096"]
        labels:
          app: "jellyfin"
```
then, I restart prometheus:
```
sudo systemctl restart prometheus
sudo systemctl status prometheus
```
Then, I check in `https://prometheus.home/targets` that I see `jellyfin`'s status being `Up`.
I have imported the prometheus data source to grafana in: Connections > Data sources > Add new data source
using `localhost:9090` as data source.


# 2025/12/06 - Monitoring server stats

I have installed `ifstat` to get the network usage from the server:
```
sudo apt install ifstat
```
I have created a new script that takes the rate in KB/s for input and output of the different networks,
in particular of `eno1` and `tailscale0`.
I have used the same structure as the `log_cpu_temperature.sh` script.
I have added this networking script to `crontab` (executed every minute).
I have also added the scripts for the CPU usage, RAM usage, and disk usage.
Then, I have added this information in the Grafana dashboard.


# 2025/12/11 - Monitor /srv disk usage and Jellyfin status

I have created a crontab job that runs every day at 3AM that reports the subdirectory sizes of `/srv`.
I have also added a job that just tries to get the metrics from Jellyfin and reports the status (up/down).
I have added this information to Grafana and created an alert to notify me when Jellyfin is down.


# 2025/12/12 - Lag in Grafana

When looking at the "Server stats" page in Grafana, it gets laggy and the CPU usage spikes to 90%.
I believe this is because Grafana needs to read CSV files with 100k lines, 
which is CPU intensive.
I have now made all logs to run every 5s instead of 1-2s, 
so that the file size for 24h can be reduced from 100k lines to 18k lines.
Now, the interface is more responsive.
I have to see if I use the 24h visualizations, if not I can further reduce the log files' size.


# 2025/12/13 - Better logs for monitoring stats

I believe that Grafana lags because it needs to process the data from the CSV log files 3 times,
as I have 3 panels for: instantaneous, last 1h, and last 24h data.
Note that Grafana updates the dashboards every 5s at the fastest mode.
To recude the processing requirements, I can create 3 different log files:
- instantaneous (point every 1-5s): a single line in the file
- last 1h (point every 5s): `1 line / 5s * 3600s = 720 lines` in the file
- last 24h (point every 30s): `1 line / 30s * 3600s / 1h * 24h = 2880 lines` in the file

The data for the "last 24h" can be the average of the points from the instantaneous of "last 1h" data.
I have coded this up and now Grafana does not lag anymore and the CPU usage is <10%.


# 2025/12/15 - Remote play from gaming PC

I have a Windows 11 tower PC with a GPU that I use for gaming. 
I want to be able to remotely connect to it so that I can hame when I am not home.
The games I play are not super fast-paced / require super low latency (e.g. first-person shooter)
but I want to minimize latency.
Another problem is that I do not want to keep my PC on while I am away.
For this latter problem, I will use "Wake on LAN", see issue [#43](https://github.com/MarcSerraPeralta/homelab/issues/43),
because I will always have my home server on and connected to the same LAN.
I have followed [this Youtube tutorial](https://m.youtube.com/watch?v=qX8KBFL0jjI&pp=ygUWd2FrZSBvbiBsYW4gd2luZG93cyAxMQ%3D%3D).
My gaming PC motherboard is "ASUS PRIME B450 M-K II".
I enter the BIOS ("del" key) and select the following:
```
BIOS > Advanced Mode > Advanced > APM Configuration > Power On By PCI-E: change to "Enabled" to turn on WoL
```
Then, I go to Windows 11 and change the following:
```
Device Manager > Network adapters > Properties > Advanced > Wake on Magic Packet: enable (also enable any other ones that seem reasonable)
Device Manager > Network adapters > Properties > Power Management > Only allow a magic packet to wake the computer
```
and I run the following command in Windows PowerShell as administrator (right click: open as administrator): 
```
powercfg /hibernate off
```
On my server, I install the following:
```
sudo apt install wakeonlan
```
Then, I have veryfied that by running: 
```
wakeonlan <MAC_address_gaming_PC>
```
I can wake up my gaming PC from both Sleep mode and Shutdown mode,
where Shutdown mode is when the PC is completely turned off. 

Then, I need to be able to remote control the gaming PC.
For that, I do not want to use AnyDesk or TeamViewer.
I have found a free and open-source software that can be self-hosted called
Moonlight (client) and Sunshine (host), see issue [#44](https://github.com/MarcSerraPeralta/homelab/issues/44).
I installed sunshine in my gaming PC and allowed to run on startup, 
so that I can log in on Windows remotely when turning it on with "Wake on LAN".
I installed moonlight in my phone. 
After completing the moonlight configuration with my gaming PC, I can connect without any problem.
I installed moonlight on my Linux Mint laptop with flatpack. 
It also works without problem.
I have also followed some of the tips in [this Sunshine configuration guide](https://www.reddit.com/r/MoonlightStreaming/comments/1nmqalh/ultimate_guide_to_configuring_moonlight_sunshine/).

I can do the full procedure as I would when playing away from home:
1. `wakeonlan ...`
1. Wait until the PC is on
1. Connect to PC using moonlight
1. Log in to Windows remotely
1. Play games
1. Shut down computer


# 2025/12/26 - Disallowed video transcoding in Jellyfin

I have disallowed video transcoding for all users in Jellyfin to avoid selecting by mistake a different codec/bitrate,
which makes the CPU usage and temperature to spike (as the iGPU does not have transcoding features).
This can be done by editing each user and unmarking the option "Allow video transcoding ...".


# 2025/12/30 - Remote gaming on my home (gaming) PC

My internet speed is around 80 Mbps (upload) and 60 Mbps (download).
I have been able to play games remotely with Moonlight + Sunshine 
(e.g. "It takes two") streaming at 1080p and 60fps without any problem.
The distance between my home and where I was playing was around 1500 km.


# 2026/01/11 - Wii emulation on my gaming PC

I have installed Dolphin (Wii emulator) in my gaming PC and downloaded "stuff" from `f"{best editor}m.{'clean' in Catalan}"`
(using ProtonVPN).
I have followed the steps from [this video](https://www.youtube.com/watch?v=ciAJMgnrGrY)
to configure Dolphin.
Now I can run Wii games on my gaming PC using my keyboard and mouse as controllers.

I have seen that Wiimotes (Wii remote controllers) can be connected to the PC
and used by Dolphin as controllers.
However, Dolphin prefers the original Wiimotes. 
I will probably buy them online.
There is also the "Dolphin bar", but I do not know if that is needed...


# 2026/01/13 - Adding disk storage to my home server (Part 1)

I currently have only 256GB of SSD storage in my home server, 
which is insuficient to store all my personal media and computer backups, in particular:
personal pictures and videos, TV shows, movies, music...
For Christmas, I got:
```
1TB SATA 2.5-inch SSD BX500 from crucial (by micron)
with reads up to 540 MB/s.
```
and
```
256GB mSATA SSD SKC600MS from Kingston
```
The plan is the following:
- 256GB mSATA
    - Ubuntu (OS) < 5GB
    - Immich backup phone < 10GB
    - Email backup < 30GB
    - Documents < 1GB
    - Jellyfin music < 50GB
    - Security webcam footage < 50GB
- 1TB SATA
    - Jellyfin shows
    - Jellyfin movies
    - Immich (full library)
    - Laptop backup

I do not plan on having a lot of shows and/or movies in Jellyfin,
only the TV shows and the seasons that I am currently watching.
This is why 1TB is enough.

I would still have an extra 256GB SATA SSD, 
which is currently used for Ubuntu and everything.
The only extra connection in my home server is a SlimSATA connector,
so I would need an adapter from SlimSATA to SATA to be able to use this extra 256GB of storage.

Before installing the new drives, 
I have backed up my home directory from my home server to my laptop using `rsync`.
I have dissasembled the required parts to access the mSATA slot following [this video](https://www.youtube.com/watch?v=pP0L6xs-QMw).
To secure the mSATA SSD, I need two M1.6 x 3mm screws that I do not currently have.
I have bought a set of screws from Amazon that will in theory arrive tomorrow.


# 2026/01/14 - Adding disk storage to my home server (Part 2)

The screws have arrived. 

Before tearing off the server and install the new storage, 
I have backed up the Grafana dashboards by going to each dashboard and selecting:
`Export > Export as code > Export for sharing externally`.

Again, I have dissasembled the required parts to access the mSATA slot following [this video](https://www.youtube.com/watch?v=pP0L6xs-QMw).
I have installed the 256GB mSATA SSD with two M1.6 x 3mm screws and 
I have also installed the 1TB SATA SSD. See pictures in the correspoding journal media directory.

To simplify the installation of Ubuntu Server 24.04 LTS in the 256GB mSATA SSD,
I have removed the 1TB SATA SSD (so that there is only a single drive).
I have tried using the same USB stick that I used for installing Ubuntu in my home server,
but it gave me the following error when I click "Try and Install Ubuntu Server": 
`error invalid magic number, you need to load kernel first`.
In the Internet, people say to disable both the Legacy Boot and Secure Boot mode in the BIOS
and to burn again the Ubuntu ISO in the USB. To burn it, I used:
```
sudo dd if=/home/marc/Downloads/ubuntu-24.04.3-live-server-amd64.iso of=/dev/sdb
```
with `/dev/sdb` being the USB device, which I have obtained from `sudo fdisk -l`.
Now, the installation worked. 
I have used the same configuration as described in 2025/10/07 but with the difference
on the storage configuration that I will not use a LVM group.
The reason is that I expanded the LVM to the max on 2025/11/19, 
so it does not make sense to use an LVM group.

# 2026/01/15 - Adding disk storage to my home server (Part 3) and reinstalling everything

Once the installation has been finished and rebooted, I have run an update:
```
sudo apt update
sudo apt upgrade
sudo apt autoremove
```
and I have turned off the server.
I have installed the 1TB SATA SSD and will proceed to permanently mount it 
(and also automatically mount it in boot) at `/srv` because it will store
the server media (from Jellyfin, Immich...).
First, I check the disks and partitions:
```
lsblk -f
```
I see that the `sdb` corresponds to the 256GB mSATA SSD and that `sda` does not have any partitions,
which corresponds to the 1TB SATA SSD.
To create a GPT partition of the 1TB SATA SSD, I use `parted`:
```
sudo parted /dev/sda
```
This opens an interactive mode, where I execute (line by line):
```
mklabel gpt
mkpart primary ext4 0% 100%
quit
```
Then I format the partition as `ext4`:
```
sudo mkfs.ext4 /dev/sda1
```
which I verify with
```
lsblk -f
```
I then make sure that `/srv` exists and that it is empty:
```
ls -A /srv
```
Get the UUID of the 1TB SATA SSD:
```
blkid /dev/sda1
```
which does not work, but I can get it from `lsblk -f`, which is
`0837a1d9-f522-401e-9a37-1546365cddcb`.
Then I add it to `/etc/fstab`:
```
sudo vim /etc/fstab
```
by adding the following line:
```
/dev/disk/by-uuid/0837a1d9-f522-401e-9a37-1546365cddcb /srv ext4 defaults,noatime 0 2
```
and then running the following to update the configuration:
```
sudo systemctl daemon-reload
```
Finally, I test that everything works:
```
sudo mount -a
df -h /srv
lsblk -f
```
I reboot the PC and recheck:
```
df -h /srv
lsblk -f
```
which works.

I have copied the configuration files in `config_files` to my home server:
```
rsync -avh config_files marc@192.168.0.50:/tmp/
```
Below is a list of the commands that I have executed to set up the home server:
```
sudo apt update
sudo apt upgrade
sudo apt autoremove

sudo timedatectl set-timezone Europe/Amsterdam
mv /tmp/config_files/.selected_editor $HOME/

# install tailscale
curl -fsSL https://tailscale.com/install.sh | sh
# configure UDP-GRO for tailscale
pconfig-udp-grorintf '#!/bin/sh\n\nethtool -K %s rx-udp-gro-forwarding on rx-gro-list off \n' "$(ip -o route get 8.8.8.8 | cut -f 5 -d " ")" | sudo tee /etc/networkd-dispatcher/routable.d/50-tailscale
sudo chmod 755 /etc/networkd-dispatcher/routable.d/50-tailscale
sudo /etc/networkd-dispatcher/routable.d/50-tailscale
test $? -eq 0 || echo 'An error occurred.'
# subnet routers for tailscale
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
# ensure firewall
sudo ufw default deny routed
sudo ufw allow ssh
sudo ufw enable
# enable tailscale
sudo tailscale up --accept-dns=false --advertise-exit-node --advertise-routes=192.168.0.0/24

# install pi-hole
sudo tailscale down
curl -sSL https://install.pi-hole.net | bash
sudo pihole setpassword
# update firewall rules for pi-hole
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 53/tcp
sudo ufw allow 53/udp
sudo ufw allow 67/tcp
sudo ufw allow 67/udp
sudo ufw allow 123/udp
sudo tailscale up
# after changing option to "Permit all origins"
sudo systemctl restart pihole-FTL
# after adding new blocklists
sudo pihole -g

# set up scripts for the server stats
mv /tmp/config_files/monitoring $HOME
sudo apt install ifstat
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_cpu_temperature.sh") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_cpu_usage.sh") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_disk_usage.sh") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_jellyfin_status.sh") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_network_usage.sh") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * /home/marc/monitoring/log_ram_usage.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * /home/marc/monitoring/log_srv_disk_usage.sh") | crontab -

# install docker for Immich
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# install Immich
mv /tmp/config_files/config_files $HOME
sudo mkdir -p /srv/immich
sudo chown -R $USER:$USER /srv/immich
mkdir -p /srv/immich/external_library
sudo usermod -aG docker $USER
newgrp docker
cd $HOME/config_files/immich-app
docker compose up -d
# set up Immich by visiting http://100.100.50.50:2283
```

I have also edited the tailnet IPv4 of my server to `100.100.50.50`, see issue [#55](https://github.com/MarcSerraPeralta/homelab/issues/55).
I have set up Immich to use Storage Template with the template being `{{album}}/{{filename}}`.
I have also copied all my personal photos to the server:
```
rsync -avh /media/marc/Samsung/images/ marc@100.100.50.50:/srv/immich/external_library/
```
It took around 5h to process around 20.000 photos and 1.200 videos. 
The job that takes the most time is OCR.


# 2026/01/16 - Retrieving `/srv` data from old SSD

I want to retrieve the data from the `/srv` directory form the old SSD,
mainly the Jellyfin media. 
A problem is that I do not have a USB-to-SATA adapter, so what I have done is the following:
```
cd $HOME/config_files/immich-app
docker compose down # stops Immich
sudo poweroff
```
Then change the 1TB SATA SSD by the old 256GB SATA SSD.
On boot, enter the BIOS to ensure to boot from the 256GB mSATA SSD.
Then, I mounted the old SSD (this was a little bit special because it was a LVM)
and transfered all the files to the mSATA.
Finally, I powered off the machine, changed the old SSD to the 1TB SSD,
turned on the server, and transfered the files from mSATA to the 1TB SSD.


# 2026/01/17 - Reinstalling everything (Part 2)

Continuing the list of commands to set up the home server:
```
# installing Grafana
sudo apt-get install apt-transport-https wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
sudo systemctl enable --now grafana-server
sudo grafana-cli plugins install yesoreyeram-infinity-datasource
sudo systemctl restart grafana-server
# default username: admin and password: admin
# create point for getting the data from HTTP
sudo mv /tmp/config_files/monitoring-data-http.service /etc/systemd/system/monitoring-data-http.service
sudo systemctl daemon-reload
sudo systemctl enable monitoring-data-http.service
sudo systemctl start monitoring-data-http.service
# edit /etc/grafana/grafana.ini to add smtp information
# import dashboards and alerts
sudo systemctl restart grafana-server

# installing jellyfin
curl https://repo.jellyfin.org/install-debuntu.sh | sudo bash
# edit /etc/jellyfin/network.xml (section about subnets to add the Tailnet)
sudo systemctl restart jellyfin
# connect to jellyfin using the tailnet IP of the server and configure it
# install plugins, including https://intro-skipper.org/manifest.json
# edit /etc/jellyfin/system.xml (enable metrics)
sudo systemctl restart jellyfin

# installing caddy
sudo apt install caddy
# sudo vim /etc/pihole/pihole.toml -> port = "8080o,80o,443os,[::]:80o,[::]:443os"
sudo systemctl stop pihole-FTL
sudo systemctl restart caddy
sudo systemctl start pihole-FTL
# add the DNS entries to pihole Local DNS Entries
# download CA certificate in laptop using: 
# ssh -t marc@myserver "sudo cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt" > root.crt

# install season tracker
sudo apt install python3.12-venv
cd $HOME/config_files
git clone https://github.com/MarcSerraPeralta/seasontracker.git
cd seasontracker
python3 -m venv venv
source venv/bin/activate
pip install .
# set up seasontracker using 'seasontracker login ...'
mv /tmp/config_files/config_files/seasontracker/my_tracked_seasons.yaml $HOME/config_files/seasontracker/my_tracked_seasons.yaml
mv /tmp/config_files/config_files/seasontracker/run_seasontracker.sh $HOME/config_files/seasontracker/run_seasontracker.sh
chmod +x $HOME/config_files/seasontracker/run_seasontracker.sh
(crontab -l 2>/dev/null; echo "0 8 1 * * /home/marc/config_files/seasontracker/run_seasontracker.sh") | crontab -
```

# 2026/01/18 - Automatic backup of personal laptop

I want to automatically back up my personal laptop on my home server, 
see issue [#23](https://github.com/MarcSerraPeralta/homelab/issues/23) for more information.

First, I create the directory to store the backups:
```
sudo mkdir -p /srv/backups
sudo chown $USER:$USER /srv/backups
mkdir /srv/backups/thinkpad
```
I have created the bash script to run the backup in `config_files/backup-to-myserver.sh`.
Remember to run `chmod +x ...` on the file so that it can be executed in the laptop.
Then I have created the file `~/.config/systemd/user/laptop-backup.service` in my latop
with the following contents:
```
[Unit]
Description=Automatic laptop backup to home server
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=%h/usuari/custom/linux/backup_options/backup-to-myserver.sh
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```
and the file `~/.config/systemd/user/laptop-backup.timer` with the following contents:
```
[Unit]
Description=Run laptop backup automatically

[Timer]
OnBootSec=15min
OnUnitActiveSec=7d
Persistent=true
RandomizedDelaySec=30min

[Install]
WantedBy=timers.target
```
Finally, I enable the automatic backup:
```
systemctl --user daemon-reload
systemctl --user enable --now laptop-backup.timer
```
and check that it is running correctly:
```
systemctl --user list-timers
systemctl --user status laptop-backup.service
```
It didn't work because I haven't set up a SSH key for the server
(so that it automatically connects without asking a password).
This can be done using:
```
ssh-copy-id -i ~/.ssh/id_ed25519.pub marc@100.100.50.50
```
Then I restart the service with:
```
systemctl --user daemon-reload
systemctl --user start laptop-backup.service
```
and this time it works.


# 2026/01/25 - Automatic email archive for Gmail

Here, I am implementing the content of issue [#25](https://github.com/MarcSerraPeralta/homelab/issues/25).
First, I am going to focus on setting up the email archive for my Gmail account.

I install `mbsync`:
```
sudo apt install isync
```
I enable IMAP by: Go to Gmail Settings > Forwarding and POP/IMAP > Set IMAP Access to Enable.
I also ensure that "Sent" and "Inbox" have "Show in IMAP" checked in the "Labels" tab in settings.
Also, I generate an App Password and store it in my server using:
```
sudo apt install gnupg
echo "your-16-char-app-password" > ~/.mbsyncpass-gmail
gpg --symmetric --cipher-algo AES256 ~/.mbsyncpass-gmail
rm ~/.mbsyncpass-gmail
```

I create the email archive directory:
```
sudo mkdir -p /srv_msata/mail-archive/gmail
sudo chown -R $USER:$USER /srv_msata/mail-archive
chmod 700 /srv_msata/mail-archive
```

Then I configure `mbsync` (`vim ~/.mbsyncrc`):
```
# GMAIL REMOTE STORAGE
IMAPStore gmail-remote
Host imap.gmail.com
User marcserraperalta@gmail.com
PassCmd "gpg --quiet --for-your-eyes-only --no-tty -d ~/.mbsyncpass-gmail.gpg"
SSLType IMAPS
CertificateFile /etc/ssl/certs/ca-certificates.crt

# LOCAL ARCHIVE STORAGE
MaildirStore gmail-local
SubFolders Verbatim
Path /srv_msata/mail-archive/gmail/
Inbox /srv_msata/mail-archive/gmail/Inbox

# ARCHIVE CHANNEL
Channel gmail
Far :gmail-remote:
Near :gmail-local:
# Only sync Inbox and Sent
Patterns "INBOX" "[Gmail]/Enviats"
Create Near
Expunge None
Sync Pull
```
I can check that it runs correctly and start archiving the emails using:
```
mbsync -Va
```

I see in the files in `/srv_msata/mail-archive/gmail/Inbox/cur/` are using 
a weird encoding for special characters. 
This may difficult `fzf` or `grep`, 
but I do not think I am going to search words with special characters.

I want to not store the big attachements.
`mbsync` does not fully support this, as it only suports not downloading
emails such that text+attachment > certain size.
This implies that if the attachment is big, the text is not downloaded.
To solve this, I have created a small bash script:
```
mkdir -p ~/config_files/email-archive
cd ~/config_files/email-archive
vim remove_big_files_from_mail-archive.sh
```
and add the following contents:
```
#!/bin/bash

ARCHIVE_DIR="/srv_msata/mail-archive/gmail"

echo "Starting mail archive cleanup: $(date)"

# Find files larger than 5MB (5120 KB) and delete them
# Target the 'cur' and 'new' directories inside Maildir
find "$ARCHIVE_DIR" -type f -size +5M -name "*" -exec echo "Deleting large email: {}" \; -exec rm {} \;

echo "Cleanup finished: $(date)"
```
Remeber to make it executable:
```
chmod +x remove_big_files_from_mail-archive.sh
```

Finally, I create a montly automatic syncromization:
```
vim ~/.config/systemd/user/mbsync-archive.service
```
with the following content:
```
[Unit]
Description=Incremental Gmail Archive Sync

[Service]
Type=oneshot
ExecStart=/usr/bin/mbsync -Va
ExecStartPost=/home/marc/config_files/email-archive/remove_big_files_from_mail-archive.sh
```
and create the timer:
```
vim ~/.config/systemd/user/mbsync-archive.timer
```
with the following content:
```
[Unit]
Description=Run Gmail Archive Sync Monthly

[Timer]
OnCalendar=monthly
Persistent=true

[Install]
WantedBy=timers.target
```
And enable the job: 
```
systemctl --user daemon-reload
systemctl --user enable --now mbsync-archive.timer
```
and check that it works:
```
systemctl --user status mbsync-archive.timer
```

Ok, there is a problem with `gnupg` because it requires to enter the passphrase.
It is not ideal, but I am going to store my Gmail App Password as plain text in my server,
but only make it visible for me:
```
echo "your-16-char-gmail-app-password" > ~/.mbsync-pw-gmail
chmod 600 ~/.mbsync-pw-gmail
```
Then, I need to update `~/.mbsyncrc` with:
```
PassCmd "cat ~/.mbsync-pw-gmail"
```
Now it works.

I had problems with the UIDVALIDITY when rerunning `mbsync` because
I have changed some parameters in the Gmail IMAP configuration
and I have removed the email archive directory in `/srv_msata`.
The thing is that `mbsync` also stores the UIDVALIDITY files in `~/mbsync/`.
The solution to the UIDVALIDITY problems is to remove the files inside `~/mbsync/`.l

The working configuration for the `~/.mbsyncrc` is:
```
# GMAIL REMOTE STORAGE
IMAPAccount gmail
Host imap.gmail.com
User marcserraperalta@gmail.com
PassCmd "cat ~/.mbsync-pw-gmail"
SSLType IMAPS
CertificateFile /etc/ssl/certs/ca-certificates.crt
SSLVersions TLSv1.2
Timeout 120

IMAPStore gmail-remote
Account gmail

# LOCAL ARCHIVE STORAGE
MaildirStore gmail-local
SubFolders Verbatim
Flatten .
Path /srv_msata/mail-archive/gmail/
Inbox /srv_msata/mail-archive/gmail/Inbox

# ARCHIVE CHANNEL
Channel gmail
Far :gmail-remote:
Near :gmail-local:
Patterns "INBOX" "[Gmail]/Enviats"
Create Near
Expunge None
Sync Pull
```


# 2026/01/29 - Update Immich to v2.5.0

The newest version of Immich now supports "Free Up Space", 
which allows to delete photos in the smartphone that have already been backed up in the server. 
This is one of the features I want in issue [#17](https://github.com/MarcSerraPeralta/homelab/issues/17).
Although it is not automatic, it is much better than what I would set up.

I have updated Immich as follows:
```
docker compose pull && docker compose up -d
docker image prune
```
Now I have v2.5.2 wich corresponds to a patched modification of v2.5.0.


# 2026/02/08 - Back up home server files in my personal computer

See issue [#59](https://github.com/MarcSerraPeralta/homelab/issues/59) for the motivation
and reasoning of the implementation.
Here I just describe the commands to set it up.

Because my home server is 24/7 active, I have created the service/timer in my laptop
to back up the files in my home server. 
Currently, I only need to back up my email archive, so the back-up script is just:
```
#!/usr/bin/bash

set -euo pipefail

REMOTE_HOST="100.100.50.50"
LOGFILE="$HOME/.local/share/myserver-backup.log"

mkdir -p "$(dirname "$LOGFILE")"

# Abort quickly if server is unreachable
if ! ping -c 1 -W 3 "$REMOTE_HOST" &>/dev/null; then
    echo "$(date): Backup skipped – home server unreachable" >> "$LOGFILE"
    exit 0
fi

# mail archive
mkdir -p $HOME/Desktop/MOVE_TO_EXTERNAL_HDD/mail-archive/
rsync -aAX --delete --numeric-ids "marc@${REMOTE_HOST}:/srv_msata/mail-archive/" $HOME/Desktop/MOVE_TO_EXTERNAL_HDD/mail-archive/ >> "$LOGFILE" 2>&1

echo "$(date): Backup completed successfully" >> "$LOGFILE"
```
which I have stored in `/home/marc/usuari/custom/linux/backup_options/backup-from-myserver.sh`,
and gave execution permissions.

I have also created the following service and timer:
- `~/.config/systemd/user/myserver-backup.service`
```
[Unit]
Description=Automatic home server backup to laptop
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=%h/usuari/custom/linux/backup_options/backup-from-myserver.sh
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```
- `~/.config/systemd/user/myserver-backup.timer`
```
[Unit]
Description=Run home server backup automatically

[Timer]
OnBootSec=15min
OnUnitActiveSec=7d
Persistent=true
RandomizedDelaySec=30min

[Install]
WantedBy=timers.target
```
and activated with:
```
systemctl --user daemon-reload
systemctl --user enable --now myserver-backup.timer
```
and check that it is working correctly:
```
systemctl --user list-timers
systemctl --user status myserver-backup.service
```


# 2026/04/05 - Moving Immich assets from internal library to external library

I have implemented a similar solution to what was described in issue [#17](https://github.com/MarcSerraPeralta/homelab/issues/17).
The complete description can be found in `config_files/config_files/immich-scripts/README.md`.

After copying all files in `immich-scripts/`, I have run the following commands:
```
sudo usermod -aG systemd-journal marc
newgrp systemd-journal
sudo chmod -R g+rwX /srv/immich/internal_library
sudo chmod g+s /srv/immich/internal_library
chmod +x $HOME/config_files/immmich-scripts/run_script.sh
(crontab -l 2>/dev/null; echo "0 4 2 * * /home/marc/config_files/immich-scripts/run_script.sh") | crontab -
```
to automatically run the script at 4am every month on day 2.


# 2026/04/06 - Installing local DNS resolver (`unbound`)

I am currently using Cloudflare to resolve the DNS requests.
To avoid DNS resolvers like Google or Cloudflare to be able to track my DNS queries,
I am installing a local DNS resolver, i.e. `unbound`.
I am following the steps in the [pi-hole documentation](https://docs.pi-hole.net/guides/dns/unbound/) for installing `unbound`.
The steps are very clear and easy to follow. 
It worked on the first try without any error.

I have added the configuration file for `unbound` in `config_files`.

I have also updated `pihole` using:
```
sudo pihole -up
```


# 2026/04/07 - Activate Windows

I activated Windows in my gaming PC following [this guide](https://massgrave.dev/).


# 2026/04/08 - Solve issue with `pihole` + `unbound`

After installing unbound, I started seeing ads that were previously blocked by `pihole`.
I believe this was caused by the fact that `unbound` had IPv6 enabled.
After changing the its configuration, I have restarted it and flushed the DNS entries from `pihole`:
```
sudo systemctl restart unbound
sudo pihole reloaddns
```
and the ads were blocked again by `pihole`.


# 2026/04/12 - Exploring Tailscale TLS certificates

I have recently discovered that Tailscale allows one to handle TLS certificates easily.
Currently, I use caddy to generate a local certificate that I need to install in all devices
if I do not want to deal with the browser's warnings saying that the connection is not secure.
This solution easily works for Linux but it has some problems in macOS and Windows, because
certificates are not handled that nicely.

The Tailscale solution is very neat if one does not own a domain name.
I currently do not own a domain name, but I am planning of owning one as 
it can costs a little less than 1€/month using reputable sources (i.e., Cloudflare).
If one has MagicDNS and HTTPS certificates enabled in Tailscale, one can get
the following domain `yourserver.tailnet-name.ts.net` and Tailscale will issue a real certificate.
Note that the tailnet name can be changed but it is not customizable.
How this works is the following:
```
Let's Encrypt --> signs cert --> ts.net domain --> trusted globally
```
which then works across everything and does not need to install local certificates.

I have chosen the following tailnet name: `piranha-wall`.
Then I have enabled HTTPS certificates in my Tailscale.
On my server, I have run
```
sudo tailscale cert myserver.piranha-wall.ts.net
```
which created two files:
```
myserver.piranha-wall.ts.net.crt
myserver.piranha-wall.ts.net.key
```
and moved to `~/config_files/tailscale/` with:
```
sudo mkdir -p /etc/caddy/certs
sudo mv *.crt /etc/caddy/certs/
sudo mv *.key /etc/caddy/certs/
sudo chown root:caddy /etc/caddy/certs/*
sudo chmod 640 /etc/caddy/certs/*
```
Then, I have updated the `etc/caddy/Caddyfile` file to:
```
# The Caddyfile is an easy way to configure your Caddy web server.                                                                       
#                                                                                                                                        
# Unless the file starts with a global options block, the first                                                                          
# uncommented line is always the address of your site.                                                                                   
#                                                                                                                                        
# To use your own domain name (with automatic HTTPS), first make                                                                         
# sure your domain's A/AAAA DNS records are properly pointed to                                                                          
# this machine's public IP, then replace ":80" below with your                                                                           
# domain name.                                                                                                                           
                                                                                                                                         
:80 {                                                                                                                                    
        # Set this path to your site's directory.                                                                                        
        root * /usr/share/caddy                                                                                                          
                                                                                                                                         
        # Enable the static file server.                                                                                                 
        file_server                                                                                                                      

        # Another common task is to set up a reverse proxy:
        # reverse_proxy localhost:8080

        # Or serve a PHP site through php-fpm:
        # php_fastcgi localhost:9000
}

# Refer to the Caddy docs for more information:
# https://caddyserver.com/docs/caddyfile

pihole.myserver.piranha-wall.ts.net {
        tls /etc/caddy/certs/myserver.piranha-wall.ts.net.crt /etc/caddy/certs/myserver.piranha-wall.ts.net.key
        @root path /
        rewrite @root /admin

        reverse_proxy 192.168.0.50:8080
}


jellyfin.myserver.piranha-wall.ts.net {
        tls /etc/caddy/certs/myserver.piranha-wall.ts.net.crt /etc/caddy/certs/myserver.piranha-wall.ts.net.key
        reverse_proxy 192.168.0.50:8096
}

immich.myserver.piranha-wall.ts.net {
        tls /etc/caddy/certs/myserver.piranha-wall.ts.net.crt /etc/caddy/certs/myserver.piranha-wall.ts.net.key
        reverse_proxy 100.100.50.50:2283
}

grafana.myserver.piranha-wall.ts.net {
        tls /etc/caddy/certs/myserver.piranha-wall.ts.net.crt /etc/caddy/certs/myserver.piranha-wall.ts.net.key
        reverse_proxy 100.100.50.50:3000
}
```
and restarted caddy:
```
sudo systemctl restart caddy
```

Here, I realized the problem with Tailscale HTTPS certificates and my setup.
I have a single machine that hosts serveral services.
Tailscale only creates a certificate for `myserver.piranha-wall.ts.net`, 
and does not work for its subdomains (e.g., `grafana.myserver.piranha-wall.ts.net`. 
I have tried creating a subdomain certificate with
```
tailscale cert grafana.myserver.piranha-wall.ts.net
```
but it does not allow me.
A solution is to host my services at `myserver.piranha-wall.ts.net/grafana`,
but I much rather prefer the link starting with `grafana....` to have nice autocompletion.
I have reverted the changes in the `Caddyfile` file and restared caddy.


# 2026/05/02 - Owning and setting up a domain name

I have followed the instructions from [this Youtube video](https://www.youtube.com/watch?v=WdTpWYTPcm8)
on how to buy a domain name from Cloudflare. 
I have chosen Cloudflare because the price is around 1€/month (cheap) and it is a respectable busines:
I can trust that Cloudflare will not try to sell my data, increase the price for renewal...

I have bought `servidoret.com`.

To set it up so that I do not have to expose my home server to the Internet, 
I am following the instructions from [this Youtube video](https://www.youtube.com/watch?v=qlcVx-k-02E&t=3s).
The trick is setting up DNS verification for the certificates.
This allows having the valid SSL certificates without having to expose my home server.

In Cloudflare, I have added the following records for `servidoret.com`:
- Type: `A`, Name: `servidoret.com`, IPv4 addres: `100.100.50.50`, Proxy status: `DNS only (reserved IP)`, TTL: `Auto`.
- Type: `CNAME`, Name: `*`, Target: `servidoret.com`, Proxy status: `Off (DNS only)`, TTL: `Auto`.

I have also created a token (`Profile > API Tokens`) with the `Edit zone DNS` template:
```
Edit zone DNS API token summary

This API token will affect the below accounts and zones, along with their respective permissions

    Marcserraperalta@gmail.com's Account
        servidoret.com - DNS:Edit
```

In my server, I need to install the Cloudflare DNS extension to Caddy:
```
sudo apt install golang-go
go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest

mkdir ~/caddy-build
cd ~/caddy-build
~/go/bin/xcaddy build --with github.com/caddy-dns/cloudflare
# check that it works:
# ./caddy list-modules | grep cloudflare

sudo systemctl stop caddy
sudo cp ./caddy /usr/bin/caddy
sudo systemctl start caddy

cd ~
rm -r ~/caddy-build/
sudo rm -r ~/go/

sudo mkdir -p /etc/systemd/system/caddy.service.d
sudo vim /etc/systemd/system/caddy.service.d/env.conf
# Add
# [Service]
# Environment=CLOUDFLARE_API_TOKEN=your_token_here
sudo systemctl daemon-reload
sudo systemctl restart caddy
# check that it works with:
# systemctl show caddy | grep CLOUDFLARE
```

In my server, I have edited the `/etc/caddy/Caddyfile` file to:
```
servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }

        # Set this path to your site's directory.                                                                                        
        root * /usr/share/caddy                                                                                                          
                                                                                                                                         
        # Enable the static file server.                                                                                                 
        file_server                                                                                                                      

        # Another common task is to set up a reverse proxy:
        # reverse_proxy localhost:8080

        # Or serve a PHP site through php-fpm:
        # php_fastcgi localhost:9000
}

pihole.servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }

        @root path /
        rewrite @root /admin

        reverse_proxy 192.168.0.50:8080
}


jellyfin.servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }
        reverse_proxy 192.168.0.50:8096
}

immich.servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }
        reverse_proxy 100.100.50.50:2283
}

grafana.servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }
        reverse_proxy 100.100.50.50:3000
}
```

Then, I restart Caddy:
```
sudo systemctl restart caddy
```
I have also formatted the Caddy file using:
```
sudo caddy fmt --config /etc/caddy/Caddyfile --overwrite
# caddy validate --config /etc/caddy/Caddyfile # to validate it
```

I can see all the subdomains correctly, however I cannot see the `servidoret.com`
website (which is the Caddy welcome page).
If I remove the `tls` block inside the `servidoret.com` block, the website loads
with HTTP (no HTTPS).

I believe the problem above was due to the browser, because I have restarted my
laptop and now the `servidoret.com` (Caddy's landing page) works with HTTPS.


# 2026/05/03 - Setting up a landing page for `servidoret.com`

Store the website and icons in:
```
sudo mkdir /var/www/homepage
sudo mkdir /var/www/homepage/icons
```
and edit the Caddy file to point to that website:
```
servidoret.com {
        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }

        # Set this path to your site's directory.                                                                                        
        root * /var/www/homepage
                                                                                                                                         
        # Enable the static file server.                                                                                                 
        file_server                                                                                                                      

        # Another common task is to set up a reverse proxy:
        # reverse_proxy localhost:8080

        # Or serve a PHP site through php-fpm:
        # php_fastcgi localhost:9000
}
```

Then I have added the file `index.html` to `/var/www/homepage/` (see `config_files/homepage`).
And I have also added the icons in the `icons/` subdirectory.

Finally, I have restarted Caddy:
```
sudo systemctl restart caddy
```


# 2026/05/09 - Setting up [matrix] server

[matrix] is a protocol for messaging. 
I will install Synapse in my home server, which is the [matrix] implementation for the server.
I am following the docker installation instructions from [the official docker image](https://hub.docker.com/r/matrixdotorg/synapse).
First, I store the config file for the docker compose in `~/config_files/synapse`:
```
services: 
  synapse: 
    image: ghcr.io/element-hq/synapse:latest 
    container_name: synapse 
    restart: unless-stopped 

    volumes: 
      - /srv/synapse:/data 
    
    environment: 
      SYNAPSE_SERVER_NAME: servidoret.com 
      SYNAPSE_REPORT_STATS: "no" 
      SYNAPSE_CONFIG_PATH: /data/homeserver.yaml    

    ports: []
```
Second, I generate the initial config to `/srv/synapse`:
```
sudo mkdir /srv/synapse
sudo chown 991:991 /srv/synapse
docker run -it --rm \
    --mount type=bind,src=/srv/synapse,dst=/data \
    -e SYNAPSE_SERVER_NAME=servidoret.com \
    -e SYNAPSE_REPORT_STATS=yes \
    matrixdotorg/synapse:latest generate
```
Then, I edit the `/srv/synapse/homeserver.yaml`:
```
server_name: "servidoret.com"
public_baseurl: "https://matrix.servidoret.com/"
pid_file: /data/homeserver.pid
listeners:
  - port: 8008
    resources:
    - compress: false
      names: [client]
    tls: false
    type: http
    x_forwarded: true
database:
  name: sqlite3
  args:
    database: /data/homeserver.db
log_config: "/data/servidoret.com.log.config"
media_store_path: /data/media_store
registration_shared_secret: "..."
report_stats: true
macaroon_secret_key: "..."
form_secret: "..."
signing_key_path: "/data/servidoret.com.signing.key"
federation_enabled: false
```
Finally, I run the docker compose with the prepared configuration file:
```
cd ~/config_files/synapse
docker compose up -d
```
Then, I need to set up the Caddy reverse proxy.
First, I need the IP of the docker image:
```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' synapse
```
which in my case is `172.19.0.2`.
Then, I add to the Caddyfile the following lines:
```
matrix.servidoret.com {
        @not_tailscale {
                not remote_ip 100.64.0.0/10
        }
        respond @not_tailscale 403

        tls {
                dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        }

        reverse_proxy 172.19.0.2:8008 {
                header_up Host {host}
                header_up X-Forwarded-Proto https
                header_up X-Forwarded-Port 443
        }
}
```
I test that the Synapse is correctly working by running:
```
curl https://matrix.servidoret.com/_matrix/client/versions
```
and getting a JSON response.
It didn't work, so I checked the logs using:
```
docker logs synapse
```
and then saw that it didn't have permissions to write a file.
I changed the line in `/srv/synapse/servidoret.com.log.config` from:
```
filename: /homeserver.log
```
to
```
filename: /data/homeserver.log
```
Doing a 
```
docker restart synapse
```
makes it work.

Then, I go to `matrix.servidoret.com` in my browser, which tells me that
I need a [matrix] client.

First, I create a new user with:
```
docker exec -it synapse register_new_matrix_user \
  -u marc \
  -p changeme \
  -a \
  -k "..." \
  http://localhost:8008
```
with `-a` making the user an admin user, `-k` the shared secred in `homeserver.yaml`,
and `-p` the password, which can be changed later.

I have installed Element as the client in my phone.
I can log in, change my password, and send messages to myself.

If I ever forget my password, I can also use my access token, which can
be found in the Element Android app in
```
Settings > Advanced settings > (enable Developer mode) > Dev Tools > Access Token
```

I have also enabled notifications via email by adding the following lines to
the `homeserver.yaml` file:
```
password_config:
  enabled: true
  localdb_enabled: true
email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: bot.servidoret@gmail.com
  smtp_pass: "apppassword"

  require_transport_security: true
  enable_tls: true

  notif_from: "Matrix <bot.servidoret@gmail.com>"
  app_name: Matrix
```
I have now linked an email to my user (using the android app).
I have logged in to `https://app.element.io`, which is the website based Element app,
and selected "Forgot password". 
I got an email to update my password, so it works.


# 2026/05/14 - Setting up bot in [matrix] server (Part 1)

I create a new user corresponding to the bot:
```
docker exec -it synapse register_new_matrix_user \
  -u bot \
  -p StrongPassword \
  -k "..." \
  http://localhost:8008
```
with `-k` the shared secred in `homeserver.yaml`.

I have tested that I can log in using the browser: https://app.element.io.
Then, I have send an inviation to my other user `marc` and now I can have a
chat between `marc` and `bot`.

Because I am using Element as my android client app for [matrix],
the encryption is enabled by default (E2EE = end-to-end encryption). 
This means that the devices need to support decryption/encryption, including my bot,
in order to decript the messages in the room.
The bot needs to store a persistent crypto store to save the keys.
Moreover, now the identity trust in [matrix] is done via cross-signing
(before it could be done with a fingerprint).
I am not sure about how this works, but it is important for chosing the Python package
to use when coding up the bot.
For example, I started trying `matrix-nio` because it supports E2E, 
but I later realized that it (currently) does not support cross-signing
which makes it super difficult (or maybe impossible) to then trust the bot's device.
I am able to set the E2E in a python script and then I am able to 
read and send messages in an encrypted room with myserlf. 
However, the messages show an icon saying that the message comes from an
unverified device and I have to set the room to allow unverified devices
to send and receive messages in Element.
For this reason, I tried `mautrix` as it supports both E2E and [cross-signing](https://github.com/mautrix/python/commit/e496c2f5a2bd74458758c1f214101364c9483f64).
However, even though it supports cross-signing,
it does not support (or it is very difficult to set up) the protocol to verify it.
In the end, I have switched back to using `matrix-nio`.
I have seen that there is an example in the GitHub repo that seems to
support emoji verification (see [this file](https://github.com/matrix-nio/matrix-nio/blob/eeace59baa634ab0ee747ba40a7a96a686a9e536/examples/verify_with_emoji.py).
However, it did not work in my case. Maybe I will try again later.

I have installed the `libolm` library required for encryption:
```
sudo apt install libolm-dev
```

I do not know how the [matrix] protocol, nor Synapse, nor Element work.
There are not a lot of examples on the Internet of setting up a bot.
Therefore, I have used Google Gemini to help me code some small scripts
showcasting a single functionality that is available for the bot.

As a general overview, these are the steps:
1. Create a user for the bot
2. Run the `prepare_bot.py` script, which generates and stores the cryptographic keys
3. Open Element and log in as the bot to invite my own user to become a "friend"
4. Run all the other small scripts to test that they work correctly

I have not done it now, but I will probably use the `python-dotenv` package,
which can easily read the values from a `.env` file.

The other thing that is missing is putting all the scripts together as a single bot.


# 2026/05/23 - Setting up bot in [matrix] server (Part 2)

I have finished coding up the bot and now it works as expected.
The scripts for processing my expenses are obviously not included in this repo.
I have set a cron job that runs the bot on the first day of every month.


# 2026/05/24 - Setting up a Minecraft server

I am using Fabric mods so I will install the Fabric Minecraft server.
I am following the [official installation guide](https://fabricmc.net/use/server/).
I have created the directory `/srv_msata/minecraft/` and transfered ownership:
```
sudo mkdir /srv_msata/minecraft
sudo chown -R $USER:$USER /srv_msata/minecraft
```
Then, I have downloaded the server app:
```
curl -OJ https://meta.fabricmc.net/v2/versions/loader/26.1.2/0.19.2/1.1.1/server/jar
```
I have notived that I do not have Java installed.
The required version is specified in [this official guide](https://wiki.fabricmc.net/player:tutorials:install_server).
For my case (headless server):
```
sudo apt install openjdk-8-jre-headless
```
Then, I just need to run the following (replace 4G by the RAM to be given to the server):
```
java -Xmx4G -jar fabric-server-mc.26.1.2-loader.0.19.2-launcher.1.1.1.jar nogui
```
OK, so there is a java version missmatch because the guide is not up to date.
I have now installed:
```
sudo apt install openjdk-25-jre-headless
```
Then it works and it tells me to agree to the EULA, which can be done by 
modifying the `eula.txt` file.
Finally, rerunning the java server command correctly creates the server.

I can install mods by copying their files into the `mods/` directory.
These are the ones I have installed:
```
Chunky-Fabric-1.5.3.jar
DistantHorizons-3.0.3-b-26.1.2-fabric-neoforge.jar
FallingTree-26.1.2-25.jar
Structory_26.1_v1.3.16.jar
Terralith_26.1_v2.6.1_Fabric.jar
cristellib-fabric-26.1.2-3.1.4.jar
fabric-api-0.149.1+26.1.2.jar
ferritecore-9.0.0-fabric.jar
lithium-fabric-0.24.2+mc26.1.2.jar
lithostitched-1.7.7-fabric-26.1.jar
t_and_t-fabric-neoforge-1.13.11.jar # towns and towers
```
and I am using Minecraft version 26.1.2.


# 2026/06/12 - Improve management of cron and services (Part 1)

I have started implementing the changes described in [issue #96](https://github.com/MarcSerraPeralta/homelab/issues/96).
I have also set `vim` as the default editor in my home server, by
```
# add the following lines to ~/.bashrc
export EDITOR=vim
export VISUAL=vim
```
Then, I have also set up `sudo` so that it maintains the preferred editor:
```
sudo EDITOR=vim visudo
```
and uncomment the line:
```
Defaults env_keep += "EDITOR VISUAL"
```

Before changing the services, I need to create a script that sends me an email.
I will use the email that I created for the server: `bot.servidoret@gmail.com`.
I will store the python script and the venv in `/opt`, in particular in:
```
/opt/notifier/...
```
because this is a service that will run and I want to have all the permisions
for the files and directories correctly set, and also I want to avoid having it
on my home directory because it can be bug prone (e.g. I start moving stuff).

I will probably also move where the monitoring data is located and put it
in some directory inside `/srv` or `/srv_msata`.


# 2026/06/13 - Improve management of cron and services (Part 2)

Continuing the management of cron and systemctl services,
```
sudo mkdir /opt/notifier
# temporarilly change permissions
sudo chown $USER:$USER /opt/notifier

# create venv in /opt/notifier
python3 -m venv /opt/notifier/venv
source /opt/notifier/venv/bin/activate
pip install --upgrade pip
pip install python-dotenv

# change permissions back to root access
sudo chown root:root -R /opt/notifier
# hide .env contents
sudo chmod 600 /opt/notifier/notifier.env
```
Then, I test that the script works correctly
```
sudo /opt/notifier/venv/bin/python /opt/notifier/notifier.py "test"
```
which works.

Now, I need create the notifier services for failure, start, and stop:
```
sudo vim /etc/systemd/system/notifier-failure@.service
sudo vim /etc/systemd/system/notifier-start@.service
sudo vim /etc/systemd/system/notifier-stop@.service
```
and paste the contents:
```
[Unit]
Description=Send failure notification for %i

[Service]
Type=oneshot
ExecStart=/opt/notifier/venv/bin/python /opt/notifier/notifier.py failure %i
```
and similarly for start and stop.
Then, I reload the `systemctl`:
```
sudo systemctl daemon-reload
```

I have first modified `caddy` to test it:
```
sudo systemctl edit caddy.service
```
and add:
```
[Unit]
Wants=notifier-start@%n
OnSuccess=notifier-stop@%n
OnFailure=notifier-failure@%n
```
Then, I reload the `systemctl`:
```
sudo systemctl daemon-reload
```

To test it, I have restarted the `caddy` service:
```
sudo systemctl restart caddy.service
```

For "always-on" services, I should populate all three `Wants`, `OnSuccess`, and `OnFailure`.
However, for "repeating" services, I should only populate `OnFailure`, because I do
not want to receive a message any time the service (correctly) starts or stops,
i.e. I just want to know if there is a failure.

I have added the `[Unit] ...` to all the following "always-on" services:
```
caddy.service
grafana-server.service
jellyfin.service
tailscaled.service
pihole-FTL.service
monitoring-data-http.service
unbound.service
weather-station-server.service
docker.service
```
For my custom "always-on" services, I have also added:
```
[Service]
Restart=always
```

Now, I will set up the "repeating" services.
I will start with the `bot_expenses.sh` cron job.

First, I will move everything to `/opt` in the same way I have done for the 
notifier script.

I create the service:
```
sudo vim /etc/systemd/system/bot-expenses.service
```
with contents:
```
[Unit]
Description=Bot for monthly expenses
OnFailure=notifier-failure@%n

[Service]
Type=oneshot
ExecStart=/opt/bot-expenses/venv/bin/python /opt/bot-expenses/bot-expenses.py
```
Then, I create the associated timer:
```
sudo vim /etc/systemd/system/bot-expenses.timer
```
with contents:
```
[Unit]
Description=Runs monthly on the 1st at 7am

[Timer]
OnCalendar=*-*-01 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```
Then I run:
```
sudo systemctl daemon-reload
sudo systemctl enable --now bot-expenses.timer
```
and check that the timer appears here:
```
systemctl list-timers
```
To really test that it works, I run:
```
sudo systemctl start bot-expenses.service
```

Now, I do the same for the Immich script and seasontracker.

Also, I have removed the jobs from crontab.


# 2026/06/19 - Store config files using Ansible

I will use `ansible` to store my config files (known as "dotfiles") because of
the reasons explained in [issue #99](https://github.com/MarcSerraPeralta/homelab/issues/99).
For my laptop, I just have a "dotfiles repository" in GitHub because they are
all stored in my home directory.

I will focus now on setting up "notifier" with ansible to test the following three things:
1. Copy files outside `$HOME`
1. Edit the permissions to these files
1. Have a password stored in one of these files

First, I clone the github repo to `$HOME/ansible`:
```
cd $HOME
git clone git@github.com:MarcSerraPeralta/myserver-dotfiles.git ansible
```
Then, I create the ansible directory structure:
```
mkdir -p ~/ansible/roles/notifier/{tasks,templates,files,handlers}
cd ~/ansible
touch site.yml inventory.ini
```
I create an encrypted `.env` file with Ansible vault:
```
sudo apt install ansible-core
ansible-vault create roles/notifier/templates/notifier.env.j2
```
and I create the main script (`main.yaml`) inside `roles/notifier/tasks`.
I also add the fixed files `script.py` and `requirements.txt` in `roles/notifier/files/`
and the ones that have variables that need to be filled in `roles/notifier/templates/`.
The directory `handlers` specify what to do when one of the files/tasks has 
been updated.
Once everything is set up, I run:
```
ansible-playbook -i inventory.ini site.yml --ask-vault-pass
```
I have tested that it works by restarting the caddy service with
```
systemctl restart caddy.service
```
and I correctly receive the emails notifying me about it.


# 2026/07/05 - Self-hosted `papra`

I have added `papra` to my home server following the Docker Compose guide in
the [official papra documentation](https://docs.papra.app/self-hosting/using-docker-compose/).
I have directly created the ansible role in [my ansible repo](https://github.com/MarcSerraPeralta/myserver-dotfiles/commit/855a7835e7d8171f7372c2d2743362a02934a914).
I have also added the following line to the Caddyfile:
```
# /etc/caddy/Caddyfile
papra.servidoret.com {
	tls {
		dns cloudflare {env.CLOUDFLARE_API_TOKEN}
	}
	reverse_proxy 100.100.50.50:1221
}
```
