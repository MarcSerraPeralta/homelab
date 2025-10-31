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
The reason for doing that is because our server will now also act as a DNS resolver for both the tailnet and the local network (because it will have pi-hole in it).
The flag is to avoid a 'recursive loop' (more info in the [Tailscale docs](https://tailscale.com/kb/1072/client-preferences#use-tailscale-dns-settings)),
which I will explain now.
First note that the device with the pi-hole acts as both a DNS server for clients and a DNS client (e.g. when searching `google.com` inside the device or doing `apt update`).
The recursion occurs when the device acts as a client, because when it tries to ask "What is the IP of `google.com`" to the DNS resolver it is basically asking itself "What is the IP og `google.com`" because it is the DNS resolver. 
This ends in a recursion loop. This happens in both the tailnet and local network as each one has their own different DNS resolver. 

For the local network, this can be solved by setting the resolver of the device hosting pi-hole to an external DNS like 8.8.8.8 (Google). 
Then, device knows that if it needs to act as a DNS client, it should look at the external DNS.

For the tailnet, one also needs to use the flag `--assign-dns=false` to ensure Tailscale doesn’t overwrite the DNS settings of the device with pi-hole from the previous paragraph with the device's own IP (leading to the mentioned recursion).

Therefore, 
- before installing pi-hole into my server, I will turn off tailnet so that first I only have to deal with the local network.
- while installing pi-hole into my server, I need to make sure to make sure to set up an external DNS (this is to avoid the recursion in my local network)
- after installing pi-hole into my server, I need to turn on tailscale with `--assign-dns=false` (to avoid the recursion in my tailnet)

# 2025/10/09 - Installing Pi-hole

Now that I know what is the correct way of setting up the pi-hole (see notes from 2025/10/08), I will install pi-hole on my server.
First, I made sure that Tailscale was down:
```
sudo tailscale down
sudo tailscale status
```
As a side comment, Tailscale was up when I booted the server, so I am going to close the corresponding GitHub issue (maybe last time I had it down before reboot so it stayed down).
The issue about the keyboard still persists.

Then, I followed the guide from the [pi-hole docs](https://docs.pi-hole.net/main/basic-install/).
- During the installation, it tells me to make sure that the server has a static IP address, which does.
- It also asks me to choose and interface: `eno1` or `tailscale0`. 
I choose `eno1` (which is the local network) because I can then configure Tailscale to use my server as DNS.
- For the upstream DNS provider, I chose `Cloudflare` because it does not store as much log info as Google.
- I included StevenBlack's unified hosts list.
- Regarding query logging, I have enabled it to check that everything works fine at the beginning, but I will most likely disable it afterwards.
 have also selected `Show everything` as privacy mode for FTL to check that everything works, but then I will turn it down to `Hide domains and clients` or `Anonymous mode`.

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
The problem is that lighttdp is using port 80 so pihole cannot use it (`sudo ss -tulnp`).
I just disabled lighttdp and restarted pihole-FTL:
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

I will not uninstall lighttdp, I will just keep it disabled.

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
There is one important thing to do so that pi-hole can be the DNS for tailnet: one needs to select "Permit all origins" so that requests from the tailnet are also answered.
By default, pi-hole only listens to local requests (i.e. from the local network), but we also want it to answer requests from the tailnet.
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
Select "Expert mode" (click on the "Basic" toggle) and set the Query Anonymization to "Hide domains: Display and store all domains as hidden".
This means that the domains are not stored and cannot be seen, which improves the privacy. 

By default, pi-hole only stores the logs for up to 91 days (see `maxDBdays` in `/etc/pihole/pihole.toml`), which is good for storage purposes.
I will leave it like this.


# 2025/10/11 - Shut down home server

I have shut down the home server because I want to clean the fans (it is a little bit noisy and bothers me).
After shutting it down, I have changed the DNS prover in the router settings to the default one (not my home server's IP).
Also, if the internet does not work for some devices, make sure that they are not connected to the tailnet.
Recall that the DNS provider for the tailnet is the home server (which is now turned off).
I could change it to the default one, but what is the point of using the tailnet if I don't have my home server turned on.
I have also made the router use only WPA2 for wireless security (before it was using both WPA2 and WPA, which is not super secure).

I have also tested the tailnet's internet speed between two countries (Spain - Netherlands) and I obtained ~80 Mbps.
The bandwidth of my spanish WiFi is 600 Mbps and the cause of the tailnet bandwidth being 80 Mbps is that my dutch internet speed is 80 Mbps.


# 2025/10/12 - Share my server with other people

I have shared my server (which I turned on) with my girlfriend so that she can also block the ads with pi-hole. 
This can be done following the instructions in the [Tailscale docs](https://tailscale.com/kb/1084/sharing). 
Note that "sharing" is not the same as inviting someone to your whole tailnet; here I am just making my server available to my girlfriend's tailnet. 
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
- the following things happen with both my keyboard and my mouse in both USB 2.0 and 3.0, thus it is not to a device nor USB type
- when being in the login page, right after plugging the keyboard, 
I get the error -110 and the things I type are not registered in the terminal 
(which initially made me believe that there was a problem with the USB connections)
- if the keyboard is plugged in before boot, I see the error -110 in the log during boot, but then in the login page, the keyboard works and I can log in.
- when being in the login page, if I plug the keyboard and wait a little bit (~5-10 seconds), 
the PC tries to connect again and again to the keyboard until it succeeds (and correctly displays the name and brand of the keyboard in the logs).
- if I have the keyboard plugged in and correctly working, plugging in the mouse works almost immediately (same vice-versa).

Seeing this, I believe that the "problem" is not actually a problem and more like a "slow process" 
(in which the PC tries to connect to the USB devices).
Because I can always connect via SSH to my server and because I do not plan on connecting any storage via USB,
I will close the corresponding issue in GitHub about this problem.


# 2025/10/23 - Mitigating fan noise

Before doing anything about the fan noise, I measured how bad it is with the microphone of my smartphone (results may not be precise):
- background (server turned off): 40-42 dB
- server on and mic at 30cm from it: 45 dB
- server on and mic at 1cm from it: 50 dB

I disassembled the CD/DVD, SDD/HDD and both fans following [this video](https://www.youtube.com/watch?v=pP0L6xs-QMw).
For the rear fan (i.e. not the one for the CPU), I did not remove the motherboard, 
I just slightly bended one of the top aluminum pieces and was enough to remove the fan.
I have cleaned the fans (disassembled) and the CPU cooler (without disassembling it) using some toilet paper.
The cleaning did not reduce that much the noise from my server (which only comes from the fans).

The other thing I wanted to do is to adapt the fan curve so that the fans are not spinning if the CPU does not reach a certain temperature.
This (in theory) can be done both from the BIOS and the OS.
I did not have luck in the BIOS because the only setting I can change about the fans is their "idle mode", which was already set to the minimum (see `journal_media`).
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
In fact, I can hear more the fridge from my kitchen (one closed door away) than the server (although my fridge is kinda noisy for a fridge).
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

Following the instructions on [the docs](https://grafana.com/blog/2025/02/05/how-to-visualize-csv-data-with-grafana/) on how to load CSV data on Grafana,
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
I have added a small snipped that serves my recorded monitoring data for HTTP requests in `/etc/systemd/system/monitoring-data-http.service`.
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
I have tried connecting the dashboard to the Grafana app in my phone but I can only do the login via HTTP (not HTTPS as the app wants),
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


# 2025/10/31 - Grafana dashboard for Immich

I have added a dashboard in Grafana for Immich, which reports the storage usage and the number of photos and videos.
This can be done using the Immich API (+ API key) through URL requests, which returns JSON data.
For more information, see [issue #21](https://github.com/MarcSerraPeralta/homelab/issues/21).

I have also solved a problem with the automatic background backup in my Xiaomi phone, see [issue #24](https://github.com/MarcSerraPeralta/homelab/issues/24).
