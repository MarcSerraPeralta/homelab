# this script is not designed to be executed blindly with ./run_setup_myserver.sh
# one should copy-paste the commands and do what the comments say
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

# automatic email archive for gmail
sudo apt install isync
mv /tmp/config_files/.mbsyncrc $HOME/.mbsyncrc
echo "your-16-char-gmail-app-password" > $HOME/.mbsync-pw-gmail
chmod 600 ~/.mbsync-pw-gmail
mkdir -p $HOME/config_files/email-archive
mv /tmp/config_files/email-archive/remove_big_files_from_mail-archive.sh $HOME/config_files/email-archive/remove_big_files_from_mail-archive.sh
chmod +x $HOME/config_files/email-archive/remove_big_files_from_mail-archive.sh
mkdir -p $HOME/.config/systemd/user/
mv /tmp/config_files/mbsync-archive.service $HOME/.config/systemd/user/mbsync-archive.service
mv /tmp/config_files/mbsync-archive.timer $HOME/.config/systemd/user/mbsync-archive.timer
sudo mkdir -p /srv_msata/mail-archive/gmail
sudo chown -R $USER:$USER /srv_msata/mail-archive
chmod 700 /srv_msata/mail-archive
systemctl --user daemon-reload
systemctl --user enable --now mbsync-archive.timer

# automatic Immich asset transfer from internal to external library
mkdir $HOME/config_files/immich-scripts
mv /tmp/config_files/config_files/immich-scripts/ $HOME/config_files/immich-scripts/
chmod +x $HOME/config_files/immich-scripts/run_script.sh
# give me permissions to edit internal library
sudo usermod -aG systemd-journal $USER
newgrp systemd-journal
sudo chmod -R g+rwX /srv/immich/internal_library
sudo chmod g+s /srv/immich/internal_library
# set up monthly script
(crontab -l 2>/dev/null; echo "0 4 2 * * /home/marc/config_files/immich-scripts/run_script.sh") | crontab -

# install unbound
sudo apt install unbound
sudo mv /tmp/config_files/pi-hole.conf /etc/unbound/unbound.conf.d/
sudo service unbound restart

# set up domain name
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

# set up home page for domain
sudo mkdir /var/www/homepage
mv /tmp/config_files/config_files/homepage/ /var/www/homepage/
sudo systemctl restart caddy

# install and set up [matrix] Synapse
sudo mkdir $HOME/config_files/synapse
mv /tmp/config_files/config_files/synapse/ $HOME/config_files/synapse/
sudo mkdir /srv/synapse
sudo chown 991:991 /srv/synapse
docker run -it --rm \
    --mount type=bind,src=/srv/synapse,dst=/data \
    -e SYNAPSE_SERVER_NAME=servidoret.com \
    -e SYNAPSE_REPORT_STATS=yes \
    matrixdotorg/synapse:latest generate
mv $HOME/config_files/synapse/homeserver.yaml /srv/synapse/
cd ~/config_files/synapse
docker compose up -d
# get IP for caddy from: docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' synapse
# check that it works: curl https://matrix.servidoret.com/_matrix/client/versions
# create an admin user
docker exec -it synapse register_new_matrix_user \
  -u admin \
  -p changeme \
  -a \
  -k "..." \
  http://localhost:8008
cd -

# set up [matrix] bot for summarizing my expenses
cd ~/config_files/synapse
docker exec -it synapse register_new_matrix_user \
  -u bot \
  -p changeme \
  -k "..." \
  http://localhost:8008
cd -
mv /tmp/config_files/config_files/matrix-bot/ $HOME/config_files/matrix-bot/
chmod +x $HOME/config_files/matrix-bot/bot_expenses.sh
# edit .env file inside matrix-bot/
# prepare venv and credentials for the bot
cd ~/config_files/matrix-bot
python3 -m venv venv_expenses
source ./venv_expenses/bin/activate
pip install -r requirements.txt
python prepare_bot.py
deactivate
sudo mkdir /srv_msata/expenses
sudo chown -R $USER:$USER /srv_msata/expenses
mkdir /srv_msata/expenses/data
mkdir /srv_msata/expenses/plots
# copy all existing data already to /srv_msata/expenses/data
chmod 700 /srv_msata/expenses
# first day of every month at 7am
(crontab -l 2>/dev/null; echo "0 7 1 * * /home/marc/config_files/matrix-bot/bot_expenses.sh") | crontab -

