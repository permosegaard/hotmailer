#!/bin/bash
# disk optimisations here
echo "*/5 * * * * root /sbin/swapoff -a" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root /bin/mount -o remount,noatime,nodiratime,nobh,nouser_xattr,barrier=0,commit=600 /" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo noop > /sys/block/vda/queue/scheduler" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo 99 > /proc/sys/vm/dirty_ratio" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo 80 > /proc/sys/vm/dirty_background_ratio" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo 360000 > /proc/sys/vm/dirty_expire_centisecs" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo 360000 > /proc/sys/vm/dirty_writeback_centisecs" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations
echo "*/5 * * * * root echo 99 > /proc/sys/vm/swappiness" | sudo tee -a /etc/cron.d/unsafe_disk_optimisations

# DDNS setup here
sudo hostnamectl set-hostname hotmailer
echo "hotmailer" | sudo tee /etc/hostname
echo "127.0.1.1 hotmailer" | sudo tee -a /etc/hosts

# Timezone setup here
echo "Europe/London" | sudo tee /etc/timezone
sudo DEBIAN_FRONTEND=noninteractive dpkg-reconfigure tzdata

# ntp setup here
sudo ntpdate pool.ntp.org
sudo apt-get install -y ntp
sudo service ntp start

# general vm setup here
sudo apt-get update
sudo apt-get upgrade -y # this can take a while but as we're invoking gcc it's hardly a problem :P

# let's setup some debconf answers here
echo wireshark-common wireshark-common/install-setuid boolean false | sudo debconf-set-selections

# install various standard tools here
sudo apt-get install -y unzip dos2unix glances iftop tshark links ncdu atop tmux
sudo apt-get install -y linux-tools-3.19.0-15-generic # perf here, tracks against installed kernel

# atop setup here
# TODO: probably needs logrotate <- possibly others
sudo sed -i 's/INTERVAL=600/INTERVAL=10/' /etc/default/atop
sudo service atop restart

### stuff here
sudo apt-get install -y python3-pip
sudo pip3 install fake-factory nltk
sudo python3 -m nltk.downloader -d /usr/local/share/nltk_data wordnet

# cleanup here
sudo apt-get autoremove -y
sudo apt-get clean
sudo find /var/lib/apt/lists -type f -exec rm -v {} \;

# FIXES: "The SSH command responded with a non-zero exit status"
true
