# 2025/06/10 - Setting up new home server (Part 1)

I just bought a HP Elitedesk 800 G1 USDT (for 50.00€) with the following specs:
```
Operating system: Windows 10 Pro
Processor Intel(R) Core(TM) i5-4590S CPU @ 3.00GHz 
Installed RAM 8 GB
Storage 224 GB SSD KINGSTON SUV400S37240G
Graphics card Intel(R) HD Graphics 4600 (113 MB)
```
which included Power Cable + Original HP AC Adapter + HP mouse.
The reason for using a mini PC as a home server is explained in issue [#3](https://github.com/MarcSerraPeralta/homelab/issues/3).
I have chosen this specific mini PC because it is cheap and the CPU has a "high" frequency (see [hardware recommendations for Tailscale](https://tailscale.com/kb/1320/performance-best-practices#machine-sizing-recommendations)) and 4 cores.

The system boots up and Windows runs correctly. 

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

